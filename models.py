import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    characters = db.relationship('Character', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    character_class = db.Column(db.String(32), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    health = db.Column(db.Integer, default=100)
    mana = db.Column(db.Integer, default=100)
    strength = db.Column(db.Integer, default=5)
    intelligence = db.Column(db.Integer, default=5)
    dexterity = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    game_state = db.relationship('GameState', backref='character', lazy=True, uselist=False)
    images = db.relationship('GameImage', backref='character', lazy=True)
    audio_files = db.relationship('CharacterAudio', backref='character', lazy=True)
    
    def __repr__(self):
        return f'<Character {self.name} (Level {self.level} {self.character_class})>'

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    current_location = db.Column(db.String(64), nullable=False)
    inventory = db.Column(db.Text, default="{}")  # JSON string of inventory items
    quest_progress = db.Column(db.Text, default="{}")  # JSON string of quest progress
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<GameState for Character {self.character_id} at {self.current_location}>'

class GameImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=False)  # Changed from String(512) to Text to handle longer URLs and SVG data
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<GameImage {self.id} for Character {self.character_id}>'

class CharacterAudio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    audio_type = db.Column(db.String(32), nullable=False, default='introduction')  # 'introduction', 'dialogue', etc.
    audio_text = db.Column(db.Text, nullable=False)  # The text that was converted to speech
    audio_data = db.Column(db.Text, nullable=False)  # Base64-encoded audio data
    voice_type = db.Column(db.String(32), nullable=False, default='onyx')  # The voice type used for the audio
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<CharacterAudio {self.id} for Character {self.character_id} ({self.audio_type})>'
