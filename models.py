import datetime
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey

class Base(DeclarativeBase):
    pass

class User(UserMixin, Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    
    characters: Mapped[list["Character"]] = relationship(back_populates="user")
    
    def __repr__(self):
        return f'<User {self.username}>'

class Character(Base):
    __tablename__ = 'character'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'))
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    character_class: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    health: Mapped[int] = mapped_column(Integer, default=100)
    mana: Mapped[int] = mapped_column(Integer, default=100)
    strength: Mapped[int] = mapped_column(Integer, default=5)
    intelligence: Mapped[int] = mapped_column(Integer, default=5)
    dexterity: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    
    game_state: Mapped["GameState"] = relationship(back_populates="character", uselist=False)
    images: Mapped[list["GameImage"]] = relationship(back_populates="character")
    audio_files: Mapped[list["CharacterAudio"]] = relationship(back_populates="character")
    user: Mapped["User"] = relationship(back_populates="characters")
    
    def __repr__(self):
        return f'<Character {self.name} (Level {self.level} {self.character_class})>'

class GameState(Base):
    __tablename__ = 'game_state'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id'))
    current_location: Mapped[str] = mapped_column(String(64), nullable=False)
    inventory: Mapped[str] = mapped_column(Text, default="{}")  # JSON string of inventory items
    quest_progress: Mapped[str] = mapped_column(Text, default="{}")  # JSON string of quest progress
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    character: Mapped["Character"] = relationship(back_populates="game_state")
    
    def __repr__(self):
        return f'<GameState for Character {self.character_id} at {self.current_location}>'

class GameImage(Base):
    __tablename__ = 'game_image'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id'))
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)  # Changed from String(512) to Text to handle longer URLs and SVG data
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    character: Mapped["Character"] = relationship(back_populates="images")
    
    def __repr__(self):
        return f'<GameImage {self.id} for Character {self.character_id}>'

class CharacterAudio(Base):
    __tablename__ = 'character_audio'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id'))
    audio_type: Mapped[str] = mapped_column(String(32), nullable=False, default='introduction')  # 'introduction', 'dialogue', etc.
    audio_text: Mapped[str] = mapped_column(Text, nullable=False)  # The text that was converted to speech
    audio_data: Mapped[str] = mapped_column(Text, nullable=False)  # Base64-encoded audio data
    voice_type: Mapped[str] = mapped_column(String(32), nullable=False, default='onyx')  # The voice type used for the audio
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    character: Mapped["Character"] = relationship(back_populates="audio_files")
    
    def __repr__(self):
        return f'<CharacterAudio {self.id} for Character {self.character_id} ({self.audio_type})>'
