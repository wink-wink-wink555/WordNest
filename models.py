from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Word(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), unique=True, nullable=False)
    marked = db.Column(db.Boolean, default=False)
    
    definitions = db.relationship('Definition', backref='word', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'word': self.word,
            'marked': self.marked,
            'definitions': [definition.to_dict() for definition in self.definitions]
        }
    
    @staticmethod
    def from_dict(word_dict):
        word = Word(word=word_dict['word'], marked=word_dict.get('marked', False))
        for def_dict in word_dict['definitions']:
            definition = Definition.from_dict(def_dict)
            word.definitions.append(definition)
        return word

class Definition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('word.id'), nullable=False)
    part_of_speech = db.Column(db.String(20), nullable=False)
    meaning = db.Column(db.Text, nullable=False)
    example = db.Column(db.Text, nullable=True)
    note = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        return {
            'part_of_speech': self.part_of_speech,
            'meaning': self.meaning,
            'example': self.example or "",
            'note': self.note or ""
        }
    
    @staticmethod
    def from_dict(definition_dict):
        return Definition(
            part_of_speech=definition_dict['part_of_speech'],
            meaning=definition_dict['meaning'],
            example=definition_dict.get('example', ""),
            note=definition_dict.get('note', "")
        ) 
