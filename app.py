import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from sqlalchemy.orm import DeclarativeBase
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize Flask app and extensions
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure database - use PostgreSQL if available, otherwise fallback to SQLite
database_url = os.environ.get("DATABASE_URL")
if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rpggame.db"
    logging.warning("DATABASE_URL not found. Using SQLite database instead.")

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Import routes after app initialization to avoid circular imports
from models import User, Character, GameState, GameImage
from game_engine import GameEngine
from ai_service import generate_text_response, generate_image

# Initialize the game engine
engine = GameEngine()

# Flask 2.0+ removes before_first_request
# We'll use with app.app_context() instead
with app.app_context():
    db.create_all()
    # Initialize game world data
    engine.initialize_game_world()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/character_creation")
def character_creation():
    return render_template("character_creation.html")

@app.route("/create_character", methods=["POST"])
def create_character():
    if "user_id" not in session:
        # Create anonymous user
        anonymous_user = User(username=f"anonymous_{os.urandom(4).hex()}")
        db.session.add(anonymous_user)
        db.session.commit()
        session["user_id"] = anonymous_user.id
    
    name = request.form.get("name")
    character_class = request.form.get("class")
    strength = int(request.form.get("strength", 5))
    intelligence = int(request.form.get("intelligence", 5))
    dexterity = int(request.form.get("dexterity", 5))
    
    # Create character
    character = Character(
        user_id=session["user_id"],
        name=name,
        character_class=character_class,
        strength=strength,
        intelligence=intelligence,
        dexterity=dexterity,
        health=100,
        mana=100,
        level=1,
        experience=0
    )
    db.session.add(character)
    db.session.commit()
    
    # Create initial game state
    game_state = GameState(
        character_id=character.id,
        current_location="starting_village",
        inventory="{}",
        quest_progress="{}"
    )
    db.session.add(game_state)
    db.session.commit()
    
    session["character_id"] = character.id
    session["game_state_id"] = game_state.id
    
    # Generate first scene
    initial_prompt = f"A new adventure begins for {name}, a level 1 {character_class}. They find themselves in a small village at the edge of a vast fantasy world. The village has thatched-roof cottages, a small market, and friendly villagers going about their day."
    
    image_url = generate_image(initial_prompt)
    
    # Save image to database
    new_image = GameImage(
        character_id=character.id,
        prompt=initial_prompt,
        image_url=image_url
    )
    db.session.add(new_image)
    db.session.commit()
    
    # Create initial scene description
    initial_description = generate_text_response(
        f"You are a fantasy RPG game master. Create a detailed introduction for a new player character named {name}, a {character_class}. Describe the starting village and mention 3 possible locations they can visit or people they can talk to. Keep the response under 300 words."
    )
    
    # Store initial scene in session
    session["current_scene"] = {
        "description": initial_description,
        "image_id": new_image.id
    }
    
    return redirect(url_for("game"))

@app.route("/game")
def game():
    if "character_id" not in session:
        return redirect(url_for("character_creation"))
    
    character_id = session["character_id"]
    character = Character.query.get(character_id)
    game_state = GameState.query.filter_by(character_id=character_id).first()
    
    # If there's no current scene in session, regenerate it
    if "current_scene" not in session:
        # Get the latest image
        latest_image = GameImage.query.filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).first()
        if latest_image:
            session["current_scene"] = {
                "description": "You continue your adventure...",
                "image_id": latest_image.id
            }
        else:
            # Fallback if no image exists
            return redirect(url_for("character_creation"))
    
    # Get current scene data
    current_scene = session["current_scene"]
    image = GameImage.query.get(current_scene["image_id"])
    
    # Get game history (last 5 images)
    history = GameImage.query.filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).limit(5).all()
    
    return render_template("game.html", 
                          character=character, 
                          game_state=game_state,
                          description=current_scene["description"],
                          image_url=image.image_url,
                          history=history)

@app.route("/command", methods=["POST"])
def process_command():
    if "character_id" not in session:
        return jsonify({"error": "No active character"}), 400
    
    command = request.form.get("command")
    character_id = session["character_id"]
    character = Character.query.get(character_id)
    game_state = GameState.query.filter_by(character_id=character_id).first()
    
    # Process command through game engine
    result = engine.process_command(command, character, game_state)
    
    # Generate text response from AI
    context = f"""
    Character: {character.name}, a level {character.level} {character.character_class}
    Location: {game_state.current_location}
    Command: {command}
    """
    response_text = generate_text_response(
        f"You are a fantasy RPG game master. Respond to the player's command: '{command}'. {context} {result.get('context', '')}. Keep the response around 200 words."
    )
    
    # Generate image for the new scene
    image_prompt = f"{character.name}, a {character.character_class}, {result.get('image_prompt', command)}. RPG game scene, fantasy setting."
    image_url = generate_image(image_prompt)
    
    # Save image to database
    new_image = GameImage(
        character_id=character.id,
        prompt=image_prompt,
        image_url=image_url
    )
    db.session.add(new_image)
    
    # Update game state if needed
    if result.get("new_location"):
        game_state.current_location = result["new_location"]
    
    # Save changes
    db.session.commit()
    
    # Update session with new scene
    session["current_scene"] = {
        "description": response_text,
        "image_id": new_image.id
    }
    
    return jsonify({
        "description": response_text,
        "image_url": image_url
    })

@app.route("/save_game", methods=["POST"])
def save_game():
    if "character_id" not in session:
        return jsonify({"error": "No active character"}), 400
    
    # Game is already being saved automatically to the database
    flash("Game saved successfully!", "success")
    return redirect(url_for("game"))

@app.route("/load_game", methods=["GET"])
def load_game():
    # Display all characters for the current user
    if "user_id" not in session:
        return redirect(url_for("index"))
    
    user_id = session["user_id"]
    characters = Character.query.filter_by(user_id=user_id).all()
    
    return render_template("load_game.html", characters=characters)

@app.route("/load_character/<int:character_id>", methods=["GET"])
def load_character(character_id):
    character = Character.query.get(character_id)
    
    if not character:
        flash("Character not found", "error")
        return redirect(url_for("index"))
    
    # Check if character belongs to current user
    if "user_id" in session and character.user_id == session["user_id"]:
        game_state = GameState.query.filter_by(character_id=character_id).first()
        
        if not game_state:
            flash("Game state not found", "error")
            return redirect(url_for("index"))
        
        # Set session variables
        session["character_id"] = character_id
        session["game_state_id"] = game_state.id
        
        # Get the latest image
        latest_image = GameImage.query.filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).first()
        
        if latest_image:
            # Create current scene
            latest_description = generate_text_response(
                f"You are a fantasy RPG game master. Create a brief description of the scene when {character.name}, a level {character.level} {character.character_class}, returns to their adventure in {game_state.current_location}. Keep it under 200 words."
            )
            
            session["current_scene"] = {
                "description": latest_description,
                "image_id": latest_image.id
            }
        
        return redirect(url_for("game"))
    
    flash("You don't have permission to load this character", "error")
    return redirect(url_for("index"))

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    db.create_all()
