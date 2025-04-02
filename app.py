import os
import json
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
import inventory_system
import game_world
import game_objectives
import filtering_toxicity

# Initialize the game engine
engine = GameEngine()

# Flask 2.0+ removes before_first_request
# We'll use with app.app_context() instead
with app.app_context():
    # Create all database tables
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
    
    # Initialize inventory based on character class
    starting_inventory = inventory_system.initialize_inventory(character.id)
    
    # Add starting equipment based on character class
    class_data = game_world.CHARACTER_CLASSES.get(character_class, {})
    
    for item_id in class_data.get("starting_equipment", []):
        inventory_system.add_item(starting_inventory, item_id)
    
    for item_id in class_data.get("starting_inventory", []):
        inventory_system.add_item(starting_inventory, item_id)
    
    # Create initial game state
    game_state = GameState(
        character_id=character.id,
        current_location=game_world.WORLD_CONFIG["starting_location"],
        inventory=json.dumps(starting_inventory),
        quest_progress=json.dumps({"completed_quests": []})
    )
    db.session.add(game_state)
    db.session.commit()
    
    session["character_id"] = character.id
    session["game_state_id"] = game_state.id
    
    # Get starting location description
    starting_location = game_world.WORLD_CONFIG["starting_location"]
    location_data = game_world.LOCATIONS[starting_location]
    
    # Generate first scene with Portuguese description
    initial_prompt = f"Uma nova aventura começa para {name}, um {class_data.get('name', character_class)} de nível 1. Eles se encontram em {location_data['name']}, {location_data['description']}"
    
    image_url = generate_image(initial_prompt)
    
    # Save image to database
    new_image = GameImage(
        character_id=character.id,
        prompt=initial_prompt,
        image_url=image_url
    )
    db.session.add(new_image)
    db.session.commit()
    
    # Create initial scene description using Portuguese prompt
    initial_description = generate_text_response(
        f"Você é o mestre de um RPG de fantasia. Crie uma introdução detalhada para um novo personagem chamado {name}, um {class_data.get('name', character_class)}. Descreva a vila inicial ({location_data['name']}) e mencione 3 possíveis locais que eles podem visitar ou pessoas com quem podem falar. Mantenha a resposta com menos de 300 palavras. Responda APENAS em português."
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
                "description": "Você continua sua aventura...",
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
        return jsonify({"error": "Nenhum personagem ativo"}), 400
    
    command = request.form.get("command")
    character_id = session["character_id"]
    character = Character.query.get(character_id)
    game_state = GameState.query.filter_by(character_id=character_id).first()
    
    # Process command through game engine
    result = engine.process_command(command, character, game_state)
    
    # Generate text response from AI (in Portuguese)
    class_data = game_world.CHARACTER_CLASSES.get(character.character_class, {})
    class_name = class_data.get('name', character.character_class)
    
    context = f"""
    Personagem: {character.name}, um {class_name} de nível {character.level}
    Localização: {game_state.current_location}
    Comando: {command}
    """
    
    # Use the context from game engine, which is already in Portuguese
    response_text = result.get('context', '')
    
    # If we need to generate AI response for complex commands
    if not response_text or "ai_response" in result:
        safe_prompt = filtering_toxicity.add_safety_prompt_prefix(
            f"Você é o mestre de um RPG de fantasia. Responda ao comando do jogador: '{command}'. {context} Mantenha a resposta com cerca de 200 palavras. Responda APENAS em português."
        )
        response_text = generate_text_response(safe_prompt)
    
    # Generate image for the new scene
    image_prompt = result.get('image_prompt', f"{character.name}, um {class_name}, {command}. Cena de RPG, cenário de fantasia.")
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
        return jsonify({"error": "Nenhum personagem ativo"}), 400
    
    # Game is already being saved automatically to the database
    flash("Jogo salvo com sucesso!", "success")
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
        flash("Personagem não encontrado", "error")
        return redirect(url_for("index"))
    
    # Check if character belongs to current user
    if "user_id" in session and character.user_id == session["user_id"]:
        game_state = GameState.query.filter_by(character_id=character_id).first()
        
        if not game_state:
            flash("Estado do jogo não encontrado", "error")
            return redirect(url_for("index"))
        
        # Set session variables
        session["character_id"] = character_id
        session["game_state_id"] = game_state.id
        
        # Get the latest image
        latest_image = GameImage.query.filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).first()
        
        if latest_image:
            # Create current scene in Portuguese
            class_data = game_world.CHARACTER_CLASSES.get(character.character_class, {})
            class_name = class_data.get('name', character.character_class)
            
            location_description = ""
            if game_state.current_location in game_world.LOCATIONS:
                location_data = game_world.LOCATIONS[game_state.current_location]
                location_description = f"em {location_data['name']}"
            
            latest_description = generate_text_response(
                f"Você é o mestre de um RPG de fantasia. Crie uma breve descrição da cena quando {character.name}, um {class_name} de nível {character.level}, retorna à sua aventura {location_description}. Mantenha com menos de 200 palavras. Responda APENAS em português."
            )
            
            session["current_scene"] = {
                "description": latest_description,
                "image_id": latest_image.id
            }
        
        return redirect(url_for("game"))
    
    flash("Você não tem permissão para carregar este personagem", "error")
    return redirect(url_for("index"))

# Database tables are already created in the previous context
