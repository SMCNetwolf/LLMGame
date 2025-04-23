import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from models import User, Character, GameState, GameImage, CharacterAudio
import secrets


from dotenv import dotenv_values
# Option 1: Using secrets (recommended)
#secret_key = secrets.token_hex(16)  # Generates a 32-character hex string (16 bytes)
# Option 2: Using os.urandom (for older Python versions)
# secret_key = os.urandom(24)  # Generates 24 random bytes (less human-readable)
#print(f"Secret Key: {secret_key}")

# Load environment variables
env_vars = dotenv_values('.env')
os.environ['SESSION_SECRET'] = env_vars['SESSION_SECRET']
#print(f"Session Secret Key: {os.environ.get('SESSION_SECRET')}")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app and extensions
db = SQLAlchemy()
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
from models import User, Character, GameState, GameImage, CharacterAudio
from game_engine import GameEngine
from ai_service import generate_text_response, generate_image, generate_character_introduction_audio
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
    
    # Generate initial hint for new players
    initial_hint = generate_contextual_hint(character, game_state, "novo jogo", {})
    
    # Gerar introdução de áudio para o personagem
    has_audio_intro = False
    audio_id = None
    
    try:
        from ai_service import generate_audio
        import logging
        
        # Gerar texto de introdução do personagem
        intro_text = generate_text_response(
            f"Crie uma introdução curta e dramática com cerca de 3 frases para {name}, um(a) {class_data.get('name', character_class)} em uma aventura de RPG. Fale na primeira pessoa, como se fosse o próprio personagem se apresentando. Mencione algo sobre a classe e a jornada que está por vir. Use linguagem épica e inspiradora. Mantenha a resposta com menos de 100 palavras."
        )
        
        # Gerar áudio para o texto de introdução
        logging.info(f"Generating audio introduction for character {name}")
        audio_data = generate_audio(intro_text, voice_type="onyx")
        
        if audio_data:
            # Salvar áudio no banco de dados
            character_audio = CharacterAudio(
                character_id=character.id,
                audio_type="introduction",
                audio_text=intro_text,
                audio_data=audio_data,
                voice_type="onyx"
            )
            db.session.add(character_audio)
            db.session.commit()
            
            has_audio_intro = True
            audio_id = character_audio.id
            logging.info(f"Audio introduction generated successfully, ID: {audio_id}")
        else:
            logging.warning("Failed to generate audio data")
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Error generating character audio: {e}")
        logging.error(traceback.format_exc())
    
    # Store initial scene in session
    session["current_scene"] = {
        "description": initial_description,
        "image_id": new_image.id,
        "has_audio_intro": has_audio_intro,
        "audio_id": audio_id,
        "hint": initial_hint  # Add initial hint to the session
    }
    
    return redirect(url_for("game"))

@app.route("/game")
def game():
    if "character_id" not in session:
        return redirect(url_for("character_creation"))
    
    character_id = session["character_id"]
    character = db.session.query(Character).get(character_id)
    game_state = db.session.query(GameState).filter_by(character_id=character_id).first()
    
    # If there's no current scene in session, regenerate it
    if "current_scene" not in session:
        # Get the latest image
        latest_image = db.session.query(GameImage).filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).first()
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
    image = db.session.query(GameImage).get(current_scene["image_id"])
    
    # Get game history (last 5 images)
    history = db.session.query(GameImage).filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).limit(5).all()
    # Check if character has an audio introduction
    has_audio_intro = False
    intro_audio_id = None    
    
    if "has_audio_intro" in current_scene and current_scene["has_audio_intro"]:
        # Check if there's an audio introduction for this character
        audio_intro = CharacterAudio.query.filter_by(character_id=character_id, audio_type="introduction").first()
        if audio_intro:
            has_audio_intro = True
            intro_audio_id = audio_intro.id
    
    # Generate a contextual hint for the initial state
    initial_hint = generate_contextual_hint(character, game_state, "olhar ao redor", {})
    
    return render_template("game.html", 
                          character=character, 
                          game_state=game_state,
                          description=current_scene["description"],
                          image_url=image.image_url,
                          history=history,
                          has_audio_intro=has_audio_intro,
                          intro_audio_id=intro_audio_id,
                          initial_hint=initial_hint)

@app.route("/command", methods=["POST"])
def process_command():
    if "character_id" not in session:
        return jsonify({"error": "Nenhum personagem ativo"}), 400
    
    command = request.form.get("command")
    character_id = session["character_id"]
    character = db.session.query(Character).get(character_id)
    game_state = db.session.query(GameState).filter_by(character_id=character_id).first()
    
    # Verificar e garantir que o inventário do personagem seja válido
    try:
        if not game_state.inventory:
            logging.warning(f"Inventário vazio para personagem {character.id}, inicializando novo")
            new_inventory = inventory_system.initialize_inventory(character.id)
            game_state.inventory = json.dumps(new_inventory)
            db.session.commit()
        else:
            # Teste se o inventário é um JSON válido
            try:
                inventory_data = json.loads(game_state.inventory)
                if not isinstance(inventory_data, dict):
                    raise ValueError("Formato de inventário inválido")
            except (json.JSONDecodeError, ValueError) as e:
                logging.error(f"Inventário inválido para personagem {character.id}: {e}")
                new_inventory = inventory_system.initialize_inventory(character.id)
                game_state.inventory = json.dumps(new_inventory)
                db.session.commit()
    except Exception as e:
        logging.error(f"Erro ao processar inventário: {e}")
        # Não deixe o erro interromper o processamento do comando
    
    # Process command through game engine
    try:
        result = engine.process_command(command, character, game_state)
    except Exception as e:
        logging.error(f"Erro no processamento do comando '{command}': {e}")
        result = {
            "context": "Houve um erro ao processar seu comando. (Algo deu errado no mundo do jogo)",
            "new_location": None,
            "image_prompt": f"{character.name} olhando confuso enquanto explora o mundo"
        }
    
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
    
    # Generate image for the new scene with character descriptions for consistency
    character_description = ""
    if hasattr(character, 'appearance'):
        character_description = character.appearance
    elif hasattr(character, 'description'):
        character_description = character.description
    else:
        # Create default character description based on class
        if character.character_class == 'guerreiro':
            character_description = f"{character.name} é um guerreiro forte e musculoso, com armadura pesada"
        elif character.character_class == 'mago':
            character_description = f"{character.name} é um mago de túnica azul com detalhes dourados"
        elif character.character_class == 'ladino':
            character_description = f"{character.name} é um ladino ágil e esguio, com vestimentas leves escuras"
        else:
            character_description = f"{character.name}, um {class_name}"
            
    image_prompt = result.get('image_prompt', f"{character_description}, {command}. Cena de RPG, cenário de fantasia medieval, estilo detalhado.")
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
    
    # Generate contextual hint based on the game state and current action
    hint = generate_contextual_hint(character, game_state, command, result)
    
    # Update session with new scene
    session["current_scene"] = {
        "description": response_text,
        "image_id": new_image.id,
        "has_audio_intro": False,  # Desativamos temporariamente o recurso de áudio
        "hint": hint
    }
    
    return jsonify({
        "description": response_text,
        "image_url": image_url,
        "current_location": game_state.current_location,
        "hint": hint
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
    characters = db.session.query(Character).filter_by(user_id=user_id).all()
    
    return render_template("load_game.html", characters=characters)

@app.route("/load_character/<int:character_id>", methods=["GET"])
def load_character(character_id):
    character = db.session.query(Character).get(character_id)
    
    if not character:
        flash("Personagem não encontrado", "error")
        return redirect(url_for("index"))
    
    # Check if character belongs to current user
    if "user_id" in session and character.user_id == session["user_id"]:
        game_state = db.session.query(GameState).filter_by(character_id=character_id).first()
        
        if not game_state:
            flash("Estado do jogo não encontrado", "error")
            return redirect(url_for("index"))
        
        # Set session variables
        session["character_id"] = character_id
        session["game_state_id"] = game_state.id
        
        # Get the latest image
        latest_image = db.session.query(GameImage).filter_by(character_id=character_id).order_by(GameImage.created_at.desc()).first()
        
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
            
            # Generate hint for returning player
            return_hint = generate_contextual_hint(character, game_state, "retornar ao jogo", {})
            
            session["current_scene"] = {
                "description": latest_description,
                "image_id": latest_image.id,
                "has_audio_intro": False,  # Desativamos temporariamente o recurso de áudio
                "hint": return_hint  # Add hint for returning players
            }
        
        return redirect(url_for("game"))
    
    flash("Você não tem permissão para carregar este personagem", "error")
    return redirect(url_for("index"))

# Endpoint para recuperar o áudio de introdução de um personagem
@app.route("/character_audio/<int:audio_id>", methods=["GET"])
def get_character_audio(audio_id):
    audio = db.session.query(CharacterAudio).get(audio_id)
    
    if not audio:
        return jsonify({"error": "Áudio não encontrado"}), 404

    # Verificar se o personagem pertence ao usuário atual
    if "user_id" in session and db.session.query(Character).get(audio.character_id).user_id == session["user_id"]:
        return jsonify({
            "audio_data": audio.audio_data,
            "audio_text": audio.audio_text,
            "voice_type": audio.voice_type
        })
    
    return jsonify({"error": "Acesso não autorizado"}), 403

# Função para gerar dicas contextuais baseadas no personagem, estado do jogo e comando atual
def generate_contextual_hint(character, game_state, command, result):
    """
    Gera uma dica contextual baseada no estado atual do jogo e na ação do jogador.
    
    Args:
        character: O objeto Character do jogador
        game_state: O objeto GameState atual
        command: O comando que o jogador executou
        result: O resultado do processamento do comando
        
    Returns:
        str: Uma dica contextual personalizada
    """
    import random
    # Extrair informações relevantes
    location_id = game_state.current_location
    character_level = character.level
    character_class = character.character_class
    character_health = character.health
    
    # Verificar o inventário (em formato JSON)
    import json
    inventory = {}
    try:
        if game_state.inventory:
            inventory = json.loads(game_state.inventory)
        else:
            # Se não houver inventário, inicialize um novo
            logging.warning(f"Inventário vazio para personagem {character.id}")
            inventory = inventory_system.initialize_inventory(character.id)
            game_state.inventory = json.dumps(inventory)
            db.session.commit()
    except Exception as e:
        logging.error(f"Erro ao carregar inventário: {e}")
        # Criar um novo inventário se ocorrer um erro
        inventory = inventory_system.initialize_inventory(character.id)
        game_state.inventory = json.dumps(inventory)
        db.session.commit()
        
    # Conjunto de dicas gerais
    general_hints = [
        "Experimente usar 'examinar' seguido de objetos para descobrir detalhes interessantes.",
        "Objetos e NPCs podem ter informações valiosas. Use 'falar com' ou 'conversar' para interagir.",
        "Guarde seu ouro para comprar itens mais poderosos nas lojas ou mercadores.",
        "Explore diferentes locais para descobrir novas missões e tesouros."
    ]
    
    # Dicas específicas baseadas no local
    location_hints = {
        "village_of_meadowbrook": [
            "A vila tem uma taverna onde você pode obter informações sobre missões e rumores.",
            "O ferreiro pode forjar novas armas se você tiver os materiais certos.",
            "Converse com os aldeões para descobrir segredos sobre a região."
        ],
        "forest_of_whispers": [
            "Ervas raras podem ser encontradas nas clareiras. Use 'procurar ervas' para encontrá-las.",
            "Os sussurros da floresta escondem segredos. Tente 'ouvir atentamente' em diferentes áreas.",
            "Cuidado com predadores escondidos. Mantenha sua saúde alta antes de explorar mais fundo."
        ],
        "ancient_ruins": [
            "Mecanismos antigos podem esconder tesouros. Procure por alavancas ou botões escondidos.",
            "Algumas paredes podem ser falsas. Tente 'examinar paredes' em busca de passagens secretas.",
            "Antigos escritos podem conter conhecimento valioso. Use 'ler' ou 'decifrar' ao encontrá-los."
        ],
        "tavern": [
            "Os clientes da taverna geralmente têm informações valiosas. Tente 'ouvir conversas'.",
            "O taverneiro pode ter missões especiais para aventureiros confiáveis.",
            "Jogos de azar podem ser uma forma rápida de ganhar (ou perder) ouro."
        ]
    }
    
    # Dicas baseadas na classe do personagem
    class_hints = {
        "guerreiro": [
            "Guerreiros podem 'intimidar' NPCs para obter vantagens em certas situações.",
            "Sua força permite mover objetos pesados. Tente 'empurrar' ou 'levantar' objetos grandes.",
            "Em combate, use 'atacar com' seguido do nome de sua arma para maior eficácia."
        ],
        "mago": [
            "Tente 'detectar magia' em locais antigos para descobrir artefatos ocultos.",
            "Seus feitiços de 'luz' podem revelar segredos em áreas escuras.",
            "A meditação pode recuperar mana mais rapidamente. Use 'meditar' quando estiver seguro."
        ],
        "ladino": [
            "Use 'esconder-se' para evitar confrontos diretos ou 'esgueirar' para passar despercebido.",
            "Suas habilidades de 'arrombar' podem abrir fechaduras sem as chaves corretas.",
            "Tente 'procurar armadilhas' antes de abrir baús ou portas suspeitas."
        ]
    }
    
    # Dicas baseadas no conteúdo do comando
    command_hint = None
    command_lower = command.lower()
    if 'ajuda' in command_lower or 'o que posso fazer' in command_lower:
        return "Você pode explorar o mundo com comandos como 'ir para', interagir com objetos e personagens usando 'examinar' ou 'falar com', e gerenciar seu inventário com 'usar item' ou 'equipar'."
    elif 'atacar' in command_lower and 'com' not in command_lower:
        command_hint = "Especifique sua arma usando 'atacar com [arma]' para maior eficácia."
    elif 'comprar' in command_lower and len(command_lower.split()) < 3:
        command_hint = "Especifique o que deseja comprar usando 'comprar [item] de [vendedor]'."
    elif 'mapa' in command_lower:
        command_hint = "Use 'ir para [local]' para viajar entre áreas conhecidas. Novos locais são descobertos pela exploração."
    elif 'inventário' in command_lower:
        if len(inventory) < 2:
            command_hint = "Seu inventário está quase vazio. Explore o mundo para encontrar ou comprar itens úteis."
    
    # Selecionar uma dica baseada na situação atual
    selected_hint = None
    
    # Se o personagem estiver com pouca saúde
    if character_health < 30:
        selected_hint = "Sua saúde está baixa! Use uma poção ou descanse para recuperá-la antes de entrar em batalha."
    # Se o personagem falou uma ação específica
    elif command_hint:
        selected_hint = command_hint
    # Dicas baseadas no local atual
    elif location_id in location_hints and location_hints[location_id]:
        selected_hint = random.choice(location_hints[location_id])
    # Dicas baseadas na classe (com menor frequência)
    elif character_class in class_hints and class_hints[character_class] and random.random() < 0.3:
        selected_hint = random.choice(class_hints[character_class])
    # Dicas gerais como fallback
    else:
        selected_hint = random.choice(general_hints)
    
    return selected_hint

# Database tables are already created in the previous context
