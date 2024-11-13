from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime, timedelta
from notion_client import Client
from dotenv import load_dotenv
import requests
import openai
import os
import bcrypt
import pymysql
import uuid
import logging
import json
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

pymysql.install_as_MySQLdb()

app = Flask(__name__)
# Cargar variables de entorno
load_dotenv()

# Credenciales de la API de Notion
NOTION_API_KEY = "ntn_K7795814785ay3XJxt84hO4XgmKtMpOa8GZmKFAUjyP4I2"
DATABASE_ID = "12d1d0aab1818036a4a9d65630a65dbe"

# Set the secret key for sessions
app.secret_key = 'your_secret_key'

# OpenAI API Key
openai.api_key = 'sk-6YfP3I2ukvVAgzmlFLk9uQ5tP0S8bZjpYGhXDWj43tT3BlbkFJ6qZWAxNGP9Zxw4UdC5Yhkhrh2pmtBMOeAhwxRF0PMA'

# MySQL configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Sebas3120@localhost/chatter_ai_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# ChatHistory model
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    session_id = db.Column(db.String(36), nullable=False)  # Añadido session_id
    role = db.Column(db.String(20), nullable=False)  # 'user' o 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# StudentProfile model
class StudentProfile(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    education_level = db.Column(db.String(255))
    learning_style = db.Column(db.String(255))
    interests = db.Column(db.Text)

    # Relación con el modelo User
    user = db.relationship('User', backref='student_profile')

# PsychologicalProfile model
class PsychologicalProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stress_level = db.Column(db.Integer)
    emotional_state = db.Column(db.String(255))
    techniques = db.Column(db.Text)

#Modelo de tareas
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending' o 'completed'

#Modelo de recursos educativos
class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    resource_type = db.Column(db.String(50), nullable=False)  # libro, video, artículo
    link = db.Column(db.String(255), nullable=False)
    tags = db.Column(db.String(255), nullable=True)

#Modelo de favoritos
class FavoriteResource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'), nullable=False)

# Modelo de Evaluaciones
class Evaluation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nombre = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)  # 'opcion-multiple', 'respuesta-corta'
    fecha_limite = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    # Opcional: Campos adicionales sugeridos
    descripcion = db.Column(db.Text, nullable=True)  # Para descripción detallada
    puntaje_maximo = db.Column(db.Integer, nullable=True)  # Puntaje máximo de la evaluación
    dificultad = db.Column(db.String(50), nullable=True)  # Nivel de dificultad: fácil, medio, difícil

    # Relación con el usuario
    user = db.relationship('User', backref='evaluations')

    # Índices (opcional para mejorar rendimiento en consultas frecuentes)
    __table_args__ = (
        db.Index('idx_user_id', 'user_id'),
    )

# Modelo de Feedback/Retroalimentación
class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    evaluacion_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comentarios = db.Column(db.String(255), nullable=True)
    nota = db.Column(db.Integer, nullable=True)

    # Relaciones con otras tablas
    evaluacion = db.relationship('Evaluation', backref='feedbacks')
    user = db.relationship('User', backref='feedbacks')

    def __repr__(self):
        return f"<Feedback(id={self.id}, evaluacion_id={self.evaluacion_id}, user_id={self.user_id}, nota={self.nota})>"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluation.id'), nullable=False)
    pregunta = db.Column(db.Text, nullable=False)
    opcion_a = db.Column(db.String(255), nullable=False)
    opcion_b = db.Column(db.String(255), nullable=False)
    opcion_c = db.Column(db.String(255), nullable=False)
    opcion_d = db.Column(db.String(255), nullable=False)
    correcta = db.Column(db.String(1), nullable=False)  # Almacenar la opción correcta (A, B, C o D)

    evaluation = db.relationship('Evaluation', backref='questions')

# Modelo de Answer (Respuestas del estudiante)
class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    respuesta_usuario = db.Column(db.String(255), nullable=False)
    correcta = db.Column(db.Boolean, default=False)

    # Relación con Question y User
    question = db.relationship('Question', backref='answers')
    user = db.relationship('User', backref='answers')

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# Configurar el logger
logging.basicConfig(level=logging.INFO)

migrate = Migrate(app, db)

# Rutas

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('educacion'))  # Redirect to the education page if logged in
    return redirect(url_for('login'))  # Redirect to login if no active session

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Buscar usuario por correo electrónico
        user = User.query.filter_by(email=email).first()

        if user:
            # Verificar si la contraseña es correcta
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                session['user'] = user.nombre
                session['user_id'] = user.id  # Guardar el ID del usuario en la sesión
                return redirect(url_for('educacion'))  # Redirige a la página de educación
            else:
                return render_template('login.html', error_login='Contraseña incorrecta.')
        else:
            return render_template('login.html', error_login='El correo no está registrado.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form['nombre']
        email = request.form['email']
        password = request.form['password']

        # Verificar si el correo ya está registrado
        if User.query.filter_by(email=email).first():
            return render_template('register.html', error_register='El correo ya está registrado.')

        # Hashear la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Crear un nuevo usuario
        new_user = User(nombre=nombre, email=email, password_hash=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

# Ruta para la página de perfil del usuario
@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user' in session:
        user = User.query.filter_by(id=session['user_id']).first()

        if request.method == 'POST':
            # Obtener datos del formulario
            nombre = request.form['nombre']
            email = request.form['email']

            # Validar si el correo electrónico ya está en uso por otro usuario
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user.id:
                return render_template('perfil.html', user=user, error="El correo ya está en uso por otro usuario.")

            # Actualizar datos del usuario en la base de datos
            user.nombre = nombre
            user.email = email
            db.session.commit()

            # Actualizar la sesión con el nuevo nombre
            session['user'] = user.nombre

            return redirect(url_for('perfil'))  # Redirige al perfil actualizado

        return render_template('perfil.html', user=user)
    return redirect(url_for('login'))

# Ruta para la página de educación con directrices para jóvenes
@app.route('/educacion', methods=['GET', 'POST'])
def educacion():
    if 'user' in session:
        if request.method == 'POST':
            tema = request.form['tema']
            # Aplicando directrices de la UGEL y MINEDU para jóvenes de 12 a 16 años
            directriz = ("Ten en cuenta las políticas de educación inclusiva, la promoción de habilidades "
                         "cognitivas, el pensamiento crítico y el desarrollo personal para estudiantes de 12 a 16 años.")
            prompt = f"{directriz} Genera contenido educativo sobre {tema}."

            # Llamar a la API de OpenAI para generar contenido educativo
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )
                contenido = response['choices'][0]['message']['content'].strip()
                return render_template('educacion.html', contenido=contenido)

            except Exception as e:
                print(f"Error al generar contenido: {e}")
                return render_template('educacion.html', error="No se pudo generar contenido.")

        return render_template('educacion.html')
    return redirect(url_for('login'))

# Ruta para la página de psicología con directrices de investigaciones y enfoques psicológicos
@app.route('/psicologia', methods=['GET', 'POST'])
def psicologia():
    if 'user' in session:
        if request.method == 'POST':
            tema = request.form['tema']
            # Aplicando directrices basadas en investigaciones y enfoques psicológicos para jóvenes
            directriz = ("Asegúrate de abordar temas relacionados con la salud mental, las emociones y los enfoques "
                         "psicológicos clave como el conductismo y el cognitivismo, enfocados en jóvenes de 12 a 16 años.")
            prompt = f"{directriz} Genera contenido psicológico sobre {tema}."

            # Llamar a la API de OpenAI para generar contenido psicológico
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    n=1,
                    stop=None,
                    temperature=0.7,
                )
                contenido = response['choices'][0]['message']['content'].strip()
                return render_template('psicologia.html', contenido=contenido)

            except Exception as e:
                print(f"Error al generar contenido: {e}")
                return render_template('psicologia.html', error="No se pudo generar contenido.")

        return render_template('psicologia.html')
    return redirect(url_for('login'))

# Ruta para la página de chat
@app.route('/chat')
def chat():
    if 'user' in session:
        return render_template('chat.html')
    return redirect(url_for('login'))

# API para el chat de la IA (con session_id)
@app.route('/api/ia', methods=['POST'])
def ia_chat():
    try:
        data = request.get_json()
        user_input = data.get('input', '')

        if not user_input:
            return jsonify({'response': 'Por favor, introduce una pregunta.'}), 400

        # Generar un session_id único
        session_id = str(uuid.uuid4())

        # Recuperar historial de chat anterior del usuario
        previous_chats = ChatHistory.query.filter_by(user_id=session['user_id']).order_by(ChatHistory.timestamp).all()
        chat_context = [{"role": "user", "content": chat.content} for chat in previous_chats]

        # Agregar la entrada del usuario actual
        chat_context.append({"role": "user", "content": user_input})

        # Interactuar con la API de OpenAI usando la nueva interfaz de chat
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=chat_context,
            max_tokens=2000,
            temperature=0.7,
        )

        # Verificar si la respuesta contiene el campo esperado
        if 'choices' in response and len(response['choices']) > 0:
            ai_response = response['choices'][0]['message']['content'].strip()
        else:
            ai_response = "Error: No se pudo generar una respuesta."

        # Guardar el chat en la base de datos, incluyendo session_id
        new_chat_user = ChatHistory(user_id=session['user_id'], session_id=session_id, role="user", content=user_input)
        db.session.add(new_chat_user)
        new_chat_ai = ChatHistory(user_id=session['user_id'], session_id=session_id, role="assistant", content=ai_response)
        db.session.add(new_chat_ai)
        db.session.commit()

        return jsonify({'response': ai_response})

    except Exception as e:
        print(f"Error al procesar la solicitud: {e}")
        return jsonify({'response': 'Error al procesar la solicitud a la API.'}), 500

# Rutas para la generación de contenido en educación y psicología
@app.route('/api/generar-contenido-educacion', methods=['POST'])
def generar_contenido_educacion():
    try:
        data = request.get_json()
        topic = data.get('input', '')

        if not topic:
            return jsonify({'response': 'Por favor, ingrese un tema.'}), 400

        prompt = (f"Aplica políticas educativas de la UGEL y MINEDU para jóvenes de 12 a 16 años, no menciones estas politicas."
                  f"Genera un contenido educativo sobre {topic}.")
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.5,
        )

        generated_content = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': generated_content})

    except Exception as e:
        print(f"Error al generar contenido educativo: {e}")
        return jsonify({'response': 'Error al procesar la solicitud a la API.'}), 500

@app.route('/api/generar-contenido-psicologia', methods=['POST'])
def generar_contenido_psicologia():
    try:
        data = request.get_json()
        topic = data.get('input', '')

        if not topic:
            return jsonify({'response': 'Por favor, ingrese un tema.'}), 400

        prompt = (f"Considera investigaciones y enfoques psicológicos claves para jóvenes de 12 a 16 años, no menciones estas politicas."
                  f"Genera un contenido psicológico sobre {topic}.")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.5,
        )

        generated_content = response['choices'][0]['message']['content'].strip()
        return jsonify({'response': generated_content})

    except Exception as e:
        print(f"Error al generar contenido psicológico: {e}")
        return jsonify({'response': 'Error al procesar la solicitud a la API.'}), 500

# Ruta para gestionar el perfil estudiantil
@app.route('/perfil_estudiantil', methods=['GET', 'POST'])
def perfil_estudiantil():
    if 'user_id' in session:
        user_id = session['user_id']
        student_profile = StudentProfile.query.filter_by(user_id=user_id).first()

        if request.method == 'POST':
            education_level = request.form['education_level']
            learning_style = request.form['learning_style']
            interests = request.form['interests']

            if student_profile:
                # Actualizar perfil estudiantil existente
                student_profile.education_level = education_level
                student_profile.learning_style = learning_style
                student_profile.interests = interests
            else:
                # Crear un nuevo perfil estudiantil si no existe
                student_profile = StudentProfile(
                    user_id=user_id,
                    education_level=education_level,
                    learning_style=learning_style,
                    interests=interests
                )
                db.session.add(student_profile)
            
            db.session.commit()
            return redirect(url_for('perfil_estudiantil'))

        # Manejar la situación cuando el perfil no existe
        if not student_profile:
            # Crear un perfil por defecto o mostrar un mensaje
            student_profile = StudentProfile(
                user_id=user_id,
                education_level='No especificado',
                learning_style='No especificado',
                interests='No especificado'
            )
            db.session.add(student_profile)
            db.session.commit()

        return render_template('perfil_estudiantil.html', profile=student_profile)
    return redirect(url_for('login'))

# Ruta para gestionar el perfil psicológico
@app.route('/perfil_psicologico', methods=['GET', 'POST'])
def perfil_psicologico():
    if 'user' in session:
        user_id = session['user_id']
        psychological_profile = PsychologicalProfile.query.filter_by(user_id=user_id).first()

        if request.method == 'POST':
            stress_level = request.form['stress_level']
            emotional_state = request.form['emotional_state']
            techniques = request.form['techniques']

            if psychological_profile:
                # Actualizar perfil psicológico
                psychological_profile.stress_level = stress_level
                psychological_profile.emotional_state = emotional_state
                psychological_profile.techniques = techniques
            else:
                # Crear un nuevo perfil psicológico
                new_profile = PsychologicalProfile(user_id=user_id, stress_level=stress_level, emotional_state=emotional_state, techniques=techniques)
                db.session.add(new_profile)
            
            db.session.commit()
            return redirect(url_for('perfil_psicologico'))

        return render_template('perfil_psicologico.html', profile=psychological_profile)
    return redirect(url_for('login'))

# Ruta para la página de recursos educativos
@app.route('/resources', methods=['GET'])
def recursos():
    # Obtener todos los recursos desde la base de datos
    recursos = Resource.query.all()
    return render_template('resources.html', recursos=recursos)

# Ruta para la página de gestión de tareas
@app.route('/tasks')
def mostrar_tareas():
    tareas = obtener_tareas()  # Recupera las tareas de Notion o la base de datos
    return render_template('tasks.html', tareas=tareas)

@app.route('/agregar_tarea', methods=['POST'])
def nueva_tarea():
    nombre = request.form.get('nombre')
    estado = request.form.get('estado', 'Pendiente')
    fecha_limite = request.form.get('fecha_limite')
    agregar_tarea(nombre, estado, fecha_limite)
    return redirect(url_for('mostrar_tareas'))

# Ruta para listar evaluaciones pendientes y retroalimentación
@app.route('/evaluaciones')
def evaluaciones():
    if 'user_id' in session:
        user_id = session['user_id']
        evaluaciones_pendientes = Evaluation.query.filter_by(user_id=user_id, completed=False).all()
        retroalimentacion = Feedback.query.join(Evaluation).filter(Evaluation.user_id == user_id).all()
        
        # Obtener el mensaje si existe
        mensaje = request.args.get('mensaje')
        
        # Obtener el ID de la evaluación creada, si existe, para redirigir al completar_evaluacion
        evaluacion_id = request.args.get('evaluacion_id')

        return render_template('evaluations.html', evaluaciones_pendientes=evaluaciones_pendientes, retroalimentacion=retroalimentacion, mensaje=mensaje, evaluacion_id=evaluacion_id)
    else:
        return redirect(url_for('login'))

#Enviar Nueva Evaluación
@app.route('/enviar_evaluacion', methods=['POST'])
def enviar_evaluacion():
    if 'user_id' in session:
        nombre = request.form.get('nombre-evaluacion')
        tipo = request.form.get('tipo-evaluacion')
        fecha_limite = datetime.utcnow() + timedelta(days=7)  # Simulamos una fecha límite en una semana

        nueva_evaluacion = Evaluation(
            user_id=session['user_id'],
            nombre=nombre,
            tipo=tipo,
            fecha_limite=fecha_limite
        )

        db.session.add(nueva_evaluacion)
        db.session.commit()

        # Redirigir a evaluations con un mensaje de éxito y la nueva evaluación creada
        return redirect(url_for('evaluaciones', mensaje="La evaluación ha sido creada exitosamente.", evaluacion_id=nueva_evaluacion.id))

    return redirect(url_for('login'))

# Ruta para completar una evaluación
@app.route('/completar_evaluacion/<int:id>', methods=['GET', 'POST'])
def completar_evaluacion(id):
    evaluacion = db.session.get(Evaluation, id)
    if not evaluacion:
        return redirect(url_for('evaluaciones'))
    if request.method == 'POST':
        # Marcar la evaluación como completada
        evaluacion.completed = True
        db.session.commit()  # Guardar cambios inmediatamente
        return redirect(url_for('evaluaciones'))
    return render_template('completar_evaluacion.html', evaluacion=evaluacion)

# API para completar una evaluación
@app.route('/api/completar_evaluacion/<int:evaluacion_id>', methods=['POST'])
def completar_evaluacion_api(evaluacion_id):
    usuario_id = request.json.get('usuario_id', 0)
    respuestas = request.json.get('respuestas', [])

    # Guardar cada respuesta del usuario
    for respuesta in respuestas:
        nueva_respuesta = Answer(
            user_id=usuario_id,
            question_id=respuesta['question_id'],
            respuesta_usuario=respuesta['respuesta_usuario'],
            correcta=(respuesta['respuesta_usuario'] == respuesta['correcta'])
        )
        db.session.add(nueva_respuesta)

    evaluacion = Evaluation.query.get(evaluacion_id)
    correctas = sum(1 for respuesta in respuestas if respuesta['respuesta_usuario'] == respuesta['correcta'])
    nota = (correctas / len(respuestas)) * 10 if respuestas else 0

    feedback = Feedback.query.filter_by(evaluacion_id=evaluacion_id, user_id=usuario_id).first()
    if feedback:
        feedback.nota = nota
        feedback.comentarios = f"Obtuviste {correctas} de {len(respuestas)} preguntas correctas."
    else:
        feedback = Feedback(
            evaluacion_id=evaluacion_id,
            user_id=usuario_id,
            nota=nota,
            comentarios=f"Obtuviste {correctas} de {len(respuestas)} preguntas correctas."
        )
        db.session.add(feedback)
    
    db.session.commit()

    return jsonify({'nota': nota, 'mensaje': 'Evaluación completada con éxito.'})

@app.route('/api/retroalimentacion_reciente', methods=['GET'])
def obtener_retroalimentacion():
    usuario_id = request.args.get('usuario_id', 0)  # Filtrar por usuario si es necesario
    retroalimentacion = Feedback.query.filter_by(usuario_id=usuario_id).all()
    return jsonify([{
        'evaluacion': fb.evaluacion.nombre,
        'comentarios': fb.comentarios,
        'nota': fb.nota,
        'id': fb.id
    } for fb in retroalimentacion])

# Ruta para generar evaluación
@app.route('/api/generar-evaluacion', methods=['POST'])
def generar_evaluacion():
    try:
        data = request.get_json()
        tema = data.get('tema', '')
        if not tema:
            return jsonify({'response': 'Por favor, ingresa un tema.'}), 400

        # Crear un prompt para OpenAI
        prompt = (
            f"Como un educador que sigue las mejores prácticas pedagógicas, "
            f"genera 10 preguntas de opción múltiple sobre el tema: {tema}. "
            f"Cada pregunta debe incentivar el pensamiento crítico, la comprensión profunda y la aplicación del conocimiento. "
            f"Proporciona 4 opciones por pregunta y la letra de la respuesta correcta separada del resto de las opciones."
        )

        # Llamar a la API de OpenAI para generar preguntas
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.7,
        )

        preguntas_generadas = response['choices'][0]['message']['content'].strip()

        # Crear la evaluación y almacenarla en la base de datos
        nueva_evaluacion = Evaluation(
            user_id=session['user_id'],
            nombre=tema,
            tipo='opcion-multiple',
            fecha_limite=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(nueva_evaluacion)
        db.session.commit()

        # Procesar las preguntas generadas y guardarlas en la base de datos
        preguntas = []
        preguntas_split = preguntas_generadas.split('\n\n')
        for pregunta_str in preguntas_split:
            partes = pregunta_str.split('\n')
            if len(partes) < 6:  # Asegúrate de que tenga suficiente contenido
                continue

            # Extraer las partes de la pregunta
            pregunta_text = partes[0].strip()
            opcion_a = partes[1].strip()
            opcion_b = partes[2].strip()
            opcion_c = partes[3].strip()
            opcion_d = partes[4].strip()
            correcta_letra = partes[5].split(':')[-1].strip()[0].upper()  # Solo la letra, ej. 'A'

            # Crear la pregunta
            nueva_pregunta = Question(
                evaluation_id=nueva_evaluacion.id,
                pregunta=pregunta_text,
                opcion_a=opcion_a,
                opcion_b=opcion_b,
                opcion_c=opcion_c,
                opcion_d=opcion_d,
                correcta=correcta_letra  # Almacenar solo la letra correcta
            )
            db.session.add(nueva_pregunta)

            preguntas.append({
                'pregunta': pregunta_text,
                'opciones': [opcion_a, opcion_b, opcion_c, opcion_d],
                'correcta': correcta_letra
            })

        db.session.commit()

        # Devolver la evaluación generada con su ID
        return jsonify({'response': preguntas, 'evaluacion_id': nueva_evaluacion.id})

    except Exception as e:
        print(f"Error al generar la evaluación: {e}")
        return jsonify({'response': f'Error al generar la evaluación: {str(e)}'}), 500

# Ruta para enviar respuestas de la evaluación
@app.route('/api/enviar-respuestas/<int:evaluacion_id>', methods=['POST'])
def enviar_respuestas(evaluacion_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado.'}), 401

    evaluacion = Evaluation.query.get(evaluacion_id)
    if not evaluacion:
        return jsonify({'feedback': 'Evaluación no encontrada.'}), 400

    respuestas_usuario = request.json.get('respuestas', {})
    correctas = 0
    total_preguntas = len(evaluacion.questions)

    # Verificar respuestas y calcular el número de correctas
    for pregunta in evaluacion.questions:
        respuesta = respuestas_usuario.get(f'pregunta-{pregunta.id}')
        if respuesta and respuesta.strip().upper() == pregunta.correcta.strip().upper():
            correctas += 1

    # Calcular la nota usando la nueva función
    nota = calcular_nota(correctas, total_preguntas)

    # Crear o actualizar el feedback para esta evaluación
    feedback = Feedback.query.filter_by(evaluacion_id=evaluacion_id, user_id=session['user_id']).first()
    if feedback:
        feedback.nota = nota
        feedback.comentarios = f"Obtuviste {correctas} de {total_preguntas} preguntas correctas."
    else:
        nuevo_feedback = Feedback(
            evaluacion_id=evaluacion_id,
            user_id=session['user_id'],
            nota=nota,
            comentarios=f"Obtuviste {correctas} de {total_preguntas} preguntas correctas."
        )
        db.session.add(nuevo_feedback)

    # Marcar la evaluación como completada
    evaluacion.completed = True
    db.session.commit()

    return jsonify({'mensaje': 'Evaluación completada.', 'nota': nota, 'correctas': correctas, 'total_preguntas': total_preguntas})

def calcular_nota(correctas, total_preguntas):
    """Calcula la nota en base a respuestas correctas y total de preguntas."""
    if total_preguntas == 0:
        return 0
    return (correctas / total_preguntas) * 10

# Generar retroalimentación personalizada
@app.route('/api/generar-retroalimentacion/<int:evaluacion_id>', methods=['POST'])
def generar_retroalimentacion(evaluacion_id):
    evaluacion = Evaluation.query.get(evaluacion_id)
    if not evaluacion:
        logging.error(f"Evaluación con ID {evaluacion_id} no encontrada.")
        return jsonify({'error': 'Evaluación no encontrada.'}), 404

    # Calcular el número de respuestas correctas y el total de preguntas
    correctas = sum(1 for pregunta in evaluacion.questions if pregunta.respuesta_correcta)
    total_preguntas = len(evaluacion.questions)
    nota = calcular_nota(correctas, total_preguntas)

    # Crear o actualizar el feedback para esta evaluación
    feedback = Feedback.query.filter_by(evaluacion_id=evaluacion_id, user_id=session['user_id']).first()
    if feedback:
        feedback.nota = nota
        feedback.comentarios = f"Obtuviste {correctas} de {total_preguntas} preguntas correctas."
    else:
        nuevo_feedback = Feedback(
            evaluacion_id=evaluacion_id,
            user_id=session['user_id'],
            nota=nota,
            comentarios=f"Obtuviste {correctas} de {total_preguntas} preguntas correctas."
        )
        db.session.add(nuevo_feedback)
    db.session.commit()

    logging.info("Retroalimentación generada y guardada correctamente.")
    return jsonify({'mensaje': 'Retroalimentación generada correctamente.', 'nota': nota, 'correctas': correctas})

# API para guardar los resultados de la evaluación completada
@app.route('/api/guardar-resultados-evaluacion', methods=['POST'])
def guardar_resultados_evaluacion():
    if 'user_id' in session:
        try:
            data = request.get_json()
            evaluacion_id = data.get('evaluacion_id')
            correctas = data.get('correctas')
            total = data.get('total')
            nota = data.get('nota')  # Calcula la nota como un porcentaje de correctas
            comentarios = data.get('comentarios')

            # Verifica si la evaluación existe
            evaluacion = Evaluation.query.get(evaluacion_id)
            if not evaluacion:
                return jsonify({'error': 'Evaluación no encontrada.'}), 404

            # Crear o actualizar el feedback
            feedback = Feedback.query.filter_by(evaluacion_id=evaluacion_id, user_id=session['user_id']).first()
            if feedback:
                feedback.nota = nota
                feedback.comentarios = comentarios
            else:
                feedback = Feedback(
                    evaluacion_id=evaluacion_id,
                    user_id=session['user_id'],
                    nota=nota,
                    comentarios=comentarios
                )
                db.session.add(feedback)

            # Guardar cambios
            db.session.commit()
            logging.info("Resultados de la evaluación guardados con éxito.")

            return jsonify({'mensaje': 'Resultados guardados con éxito.'})

        except Exception as e:
            logging.error(f"Error al guardar los resultados de la evaluación: {e}")
            return jsonify({'error': 'Error al guardar los resultados.'}), 500

    return jsonify({'error': 'No autorizado.'}), 401

# Mostrar retroalimentación
@app.route('/evaluacion/feedback/<int:evaluacion_id>', methods=['GET'])
def mostrar_feedback(evaluacion_id):
    if 'user_id' not in session:
        return jsonify({'feedback': 'No autorizado.'}), 401

    # Obtener la evaluación y el feedback asociado
    evaluacion = db.session.get(Evaluation, evaluacion_id)
    feedback = Feedback.query.filter_by(evaluacion_id=evaluacion_id, user_id=session['user_id']).first()

    if not evaluacion or not feedback:
        return jsonify({'feedback': 'Evaluación o retroalimentación no encontrada.'}), 400

    # Renderiza la plantilla con la evaluación y el feedback
    return render_template('mostrar_feedback.html', evaluacion=evaluacion, feedback=feedback)

@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    if 'user_id' in session:
        previous_chats = ChatHistory.query.filter_by(user_id=session['user_id']).order_by(ChatHistory.timestamp).all()
        history = [{'user_input': chat.content, 'ai_response': '' if chat.role == 'user' else chat.content} for chat in previous_chats]
        return jsonify({'history': history})
    else:
        return jsonify({'error': 'No autorizado.'}), 401

@app.route('/editar_perfil_educativo', methods=['GET', 'POST'])
def editar_perfil_educativo():
    if 'user_id' in session:
        user_id = session['user_id']
        student_profile = StudentProfile.query.filter_by(user_id=user_id).first()

        if request.method == 'POST':
            # Obtener datos del formulario
            education_level = request.form.get('education_level')
            learning_style = request.form.get('learning_style')
            interests = request.form.get('interests')

            if student_profile:
                # Actualizar los datos del perfil educativo
                student_profile.education_level = education_level
                student_profile.learning_style = learning_style
                student_profile.interests = interests
            else:
                # Si el perfil no existe, creamos uno nuevo
                new_profile = StudentProfile(
                    user_id=user_id,
                    education_level=education_level,
                    learning_style=learning_style,
                    interests=interests
                )
                db.session.add(new_profile)

            db.session.commit()
            return redirect(url_for('perfil_estudiantil'))  # Redirigir al perfil después de la actualización

        return render_template('editar_perfil_educativo.html', profile=student_profile)
    return redirect(url_for('login'))

# Ruta para crear una nueva tarea
@app.route('/nueva_tarea', methods=['GET', 'POST'])
def nueva_tarea_form():
    if request.method == 'POST':
        # Debug: Imprime los valores recibidos
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority'] if request.form['priority'] in ["Alta", "Media", "Baja"] else "Alta"
        status = request.form['status'] if request.form['status'] in ["Sin empezar", "En progreso", "Completada"] else "Sin empezar"

        print(f"Title: {title}, Description: {description}, Due Date: {due_date}, Priority: {priority}, Status: {status}")
        
        # Llama a la función para agregar la tarea en Notion
        agregar_tarea(title, description, due_date, priority, status)
        return redirect(url_for('mostrar_tareas'))
    
    return render_template('nueva_tarea.html')

def agregar_tarea(title, description, due_date, priority, status):
    url = f"https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": [{"text": {"content": description}}]},
            "Due Date": {"date": {"start": due_date}},
            "Priority": {"select": {"name": priority}}, 
            "Status": {"status": {"name": status}}  # Configurado correctamente como status
        }
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al agregar tarea a Notion: {response.status_code}")
        print("Detalle del error:", response.json())
        return None

# Función para obtener todas las tareas de Notion
def obtener_tareas():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
  
    response = requests.post(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        tareas = []
        for item in data.get("results", []):
            tarea = {
                "id": item.get("id"),
                "title": item["properties"]["Name"]["title"][0]["text"]["content"],
                "description": item["properties"]["Description"]["rich_text"][0]["text"]["content"] if item["properties"]["Description"]["rich_text"] else "",
                "due_date": item["properties"]["Due Date"]["date"]["start"] if item["properties"]["Due Date"]["date"] else "Sin fecha",
                "priority": item["properties"]["Priority"]["select"]["name"] if "select" in item["properties"]["Priority"] else "No especificado",
                "status": item["properties"]["Status"]["status"]["name"] if "status" in item["properties"]["Status"] else "No especificado"
            }
            tareas.append(tarea)
        return tareas
    else:
        print(f"Error al conectar con Notion: {response.status_code}")
        return []

def obtener_tarea_por_id(task_id):
    url = f"https://api.notion.com/v1/pages/{task_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        tarea = {
            "id": task_id,
            "title": data["properties"]["Name"]["title"][0]["text"]["content"],
            "description": data["properties"]["Description"]["rich_text"][0]["text"]["content"] if data["properties"]["Description"]["rich_text"] else "",
            "due_date": data["properties"]["Due Date"]["date"]["start"] if data["properties"]["Due Date"]["date"] else "Sin fecha",
            "priority": data["properties"]["Priority"]["select"]["name"] if "select" in data["properties"]["Priority"] else "No especificado",
            "status": data["properties"]["Status"]["status"]["name"] if "status" in data["properties"]["Status"] else "No especificado"
        }
        return tarea
    else:
        print(f"Error al obtener la tarea de Notion: {response.status_code}")
        return None

def actualizar_tarea(task_id, title, description, due_date, priority, status):
    url = f"https://api.notion.com/v1/pages/{task_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Description": {"rich_text": [{"text": {"content": description}}]},
            "Due Date": {"date": {"start": due_date}},
            "Priority": {"select": {"name": priority}}, 
            "Status": {"status": {"name": status}}  # Cambiado a "status" para que coincida con Notion
        }
    }

    response = requests.patch(url, headers=headers, json=data)
    
    if response.status_code == 200:
        print("Tarea actualizada correctamente en Notion.")
    else:
        print(f"Error al actualizar la tarea en Notion: {response.status_code}")
        print("Detalle del error:", response.json())
    
# Ruta para editar una tarea existente
@app.route('/editar_tarea/<string:task_id>', methods=['GET', 'POST'])
def editar_tarea(task_id):
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        status = request.form['status']

        # Actualiza la tarea en Notion
        actualizar_tarea(task_id, title, description, due_date, priority, status)
        return redirect(url_for('mostrar_tareas'))
    
    tarea = obtener_tarea_por_id(task_id)
    return render_template('editar_tarea.html', tarea=tarea)

@app.route('/eliminar_tarea/<string:task_id>', methods=['POST'])
def eliminar_tarea(task_id):
    url = f"https://api.notion.com/v1/blocks/{task_id}"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": "2022-06-28"
    }
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 200:
        print("Tarea eliminada correctamente.")
    else:
        print(f"Error al eliminar la tarea: {response.status_code}")
    
    return redirect(url_for('mostrar_tareas'))

@app.route('/api/recursos', methods=['GET'])
def obtener_recursos():
    recursos = Resource.query.all()
    recursos_json = [{
        'id': r.id,
        'title': r.title,
        'description': r.description,
        'resource_type': r.resource_type,
        'link': r.link,
        'tags': r.tags
    } for r in recursos]
    return jsonify(recursos_json)

@app.route('/api/recurso/<int:id>', methods=['PUT'])
def actualizar_recurso(id):
    data = request.get_json()
    recurso = Resource.query.get(id)

    if not recurso:
        return jsonify({'error': 'Recurso no encontrado.'}), 404

    recurso.title = data.get('title', recurso.title)
    recurso.description = data.get('description', recurso.description)
    recurso.resource_type = data.get('resource_type', recurso.resource_type)
    recurso.link = data.get('link', recurso.link)
    recurso.tags = data.get('tags', recurso.tags)

    db.session.commit()
    return jsonify({'message': 'Recurso actualizado exitosamente.'})

@app.route('/api/recurso/<int:id>', methods=['DELETE'])
def eliminar_recurso(id):
    recurso = Resource.query.get(id)

    if not recurso:
        return jsonify({'error': 'Recurso no encontrado.'}), 404

    db.session.delete(recurso)
    db.session.commit()
    return jsonify({'message': 'Recurso eliminado exitosamente.'})

def parse_resource_data(contenido):
    # Aquí parseas el contenido generado por OpenAI para extraer título, descripción, tipo, y link.
    # Esta función deberá ajustarse según el formato del texto que OpenAI genere.
    return {
        'title': 'Ejemplo de Título',
        'description': 'Descripción generada para el recurso educativo.',
        'type': 'Artículo',  # Tipo de recurso educativo
        'link': 'https://example.com',  # Enlace relacionado
        'tags': 'educación, ciencia'  # Etiquetas opcionales
    }

@app.route('/api/buscar-recursos', methods=['GET'])
def buscar_recursos():
    tema = request.args.get('tema')
    tipo = request.args.get('tipo')

    # Filtrar según parámetros recibidos
    query = Resource.query
    if tema:
        query = query.filter(Resource.tags.ilike(f"%{tema}%"))
    if tipo:
        query = query.filter_by(resource_type=tipo)

    recursos = query.all()

    # Serializar los resultados
    resultados = [{
        'title': recurso.title,
        'description': recurso.description,
        'link': recurso.link,
        'type': recurso.resource_type,
        'tags': recurso.tags
    } for recurso in recursos]

    return jsonify(resultados) if resultados else jsonify({'message': 'No se encontraron recursos para los criterios proporcionados.'}), 200

# Ruta para generar un recurso educativo
@app.route('/api/generar-recurso', methods=['POST'])
def generar_recurso():
    data = request.get_json()
    tema = data.get('tema', '')

    if not tema:
        return jsonify({'error': 'El tema es requerido'}), 400

    # Prompt para generar descripción del recurso con OpenAI
    prompt = f"Genera un recurso educativo de alta calidad sobre {tema}. Indica si es un artículo, libro, o video y proporciona una breve descripción y un enlace de referencia."

    try:
        # Llamada a la API de OpenAI para generar el contenido
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
        )
        
        # Extracción del contenido de la respuesta
        content = response.choices[0].message['content'].strip()
        
        # Parsear el contenido generado
        resource_title = f"Recurso sobre {tema}"
        resource_description = content
        resource_type = "Artículo"  # Tipo ajustable según el contenido generado
        resource_link = "https://ejemplo.com/recurso"

        # Crear y guardar el recurso en la base de datos
        new_resource = Resource(
            title=resource_title,
            description=resource_description,
            resource_type=resource_type,
            link=resource_link,
            tags=tema
        )
        db.session.add(new_resource)
        db.session.commit()

        return jsonify({'message': 'Recurso generado exitosamente', 'resource': {
            'title': resource_title,
            'description': resource_description,
            'link': resource_link,
            'type': resource_type
        }})

    except Exception as e:
        print(f"Error al generar el recurso: {e}")
        return jsonify({'error': f'No se pudo generar el recurso: {str(e)}'}), 500

# Iniciar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
