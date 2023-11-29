from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://marcelo130102:juansurco1301@marcelo130102.mysql.pythonanywhere-services.com/store'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Agrega esta línea para desactivar el seguimiento de modificaciones
app.config['SECRET_KEY'] = 'una_clave_secreta_aleatoria'
db = SQLAlchemy(app)

# Modelos
class Peliculas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    director = db.Column(db.String(255))
    año = db.Column(db.Integer)
    precio_alquiler = db.Column(db.Float)
    disponible = db.Column(db.Boolean)
    sinopsis = db.Column(db.Text)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password_k = db.Column(db.String(255), nullable=False)

class Compra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fecha_compra = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total = db.Column(db.Float, nullable=False)

class CompraItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compra.id'), nullable=False)
    pelicula_id = db.Column(db.Integer, db.ForeignKey('peliculas.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Float, nullable=False)

with app.app_context():
    db.create_all()


# Configuración de Flask-Admin
admin = Admin(app, name='admin', template_mode='bootstrap3')
admin.add_view(ModelView(Peliculas, db.session))
admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Compra, db.session))
admin.add_view(ModelView(CompraItem, db.session))

# Rutas existentes
@app.route("/")
def main():
    peliculas = Peliculas.query.all()
    return render_template('index.html', peliculas=peliculas)

@app.route('/pelicula/<int:pelicula_id>')
def ver_pelicula(pelicula_id):
    pelicula = Peliculas.query.get(pelicula_id)
    return render_template('detalles.html', pelicula=pelicula)

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/agregar_pelicula', methods=['POST'])
def agregar_pelicula():
    data = request.get_json()
    
    nueva_pelicula = Peliculas(
        nombre=data['nombre'],
        director=data['director'],
        año=data['año'],
        precio_alquiler=data['precio_alquiler'],
        disponible=data['disponible']
    )

    db.session.add(nueva_pelicula)
    db.session.commit()

    return jsonify({'mensaje': 'Película agregada correctamente'})

@app.route('/send_login', methods=['POST'])
def send_login():
    data = request.get_json()
    user = Users.query.filter_by(email=data['email']).first()

    if user:
        if user.password_k == data['password']:
            return jsonify({'mensaje': 'Bienvenido', 'status': 'autorizado'})
        else:
            return jsonify({'mensaje': 'Contraseña incorrecta', 'status': 'no_autorizado'})
    else:
        return jsonify({'mensaje': 'Usuario no encontrado'})
        
# Carrito de compras

@app.route('/agregar_al_carrito/<int:pelicula_id>', methods=['POST'])
def agregar_al_carrito(pelicula_id):
    # Obtener el carrito del almacenamiento local o inicializarlo
    carrito = session.get('carrito', [])
    
    # Agregar la película al carrito
    carrito.append(pelicula_id)
    
    # Actualizar el carrito en el almacenamiento local
    session['carrito'] = carrito

    return jsonify({'mensaje': 'Película agregada al carrito'})

# Nueva ruta para ver el contenido del carrito
@app.route('/ver_carrito')
def ver_carrito():
    # Obtener el carrito del almacenamiento local
    carrito = session.get('carrito', [])

    # Obtener las películas en el carrito
    peliculas_en_carrito = [Peliculas.query.get(pelicula_id) for pelicula_id in carrito]

    return render_template('carrito.html', peliculas=peliculas_en_carrito)



# Ruta para completar la compra
@app.route('/completar_compra', methods=['POST'])
def completar_compra():
    # Obtener el carrito del almacenamiento local
    data = request.get_json()
    carrito = data.get('carrito', [])
    print(carrito)

    # Verificar si hay elementos en el carrito
    if not carrito:
        return jsonify({'mensaje': 'El carrito está vacío'}), 400

    # Crear una nueva compra en la base de datos
    nueva_compra = Compra(usuario_id=1, fecha_compra=datetime.utcnow(), total=0)
    db.session.add(nueva_compra)
    db.session.commit()

    total_compra = 0

    # Añadir cada elemento del carrito como un ítem de compra
    for pelicula_id in carrito:
        pelicula = Peliculas.query.get(pelicula_id)

        if pelicula:
            cantidad = carrito.count(pelicula_id)
            precio_unitario = pelicula.precio_alquiler
            total_item = cantidad * precio_unitario

            # Crear un nuevo ítem de compra en la base de datos
            nuevo_item = CompraItem(compra_id=nueva_compra.id, pelicula_id=pelicula_id, cantidad=cantidad, precio_unitario=precio_unitario)
            db.session.add(nuevo_item)

            total_compra += total_item

    # Actualizar el total de la compra
    nueva_compra.total = total_compra
    db.session.commit()

    # Limpiar el carrito después de completar la compra
    session.pop('carrito', None)

    return jsonify({'mensaje': 'Compra completada con éxito'}), 200


@app.route('/inicializar_db')
def inicializar_db():
    # Inserciones en la tabla Peliculas
    peliculas_data = [
        {'nombre': 'Pelicula1', 'director': 'Director1', 'año': 2020, 'precio_alquiler': 9.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula1'},
        {'nombre': 'Pelicula2', 'director': 'Director2', 'año': 2021, 'precio_alquiler': 8.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula2'},
        {'nombre': 'Pelicula3', 'director': 'Director3', 'año': 2019, 'precio_alquiler': 7.99, 'disponible': False, 'sinopsis': 'Sinopsis de Pelicula3'},
        {'nombre': 'Pelicula4', 'director': 'Director1', 'año': 2022, 'precio_alquiler': 10.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula4'},
        {'nombre': 'Pelicula5', 'director': 'Director2', 'año': 2020, 'precio_alquiler': 8.49, 'disponible': False, 'sinopsis': 'Sinopsis de Pelicula5'},
        {'nombre': 'Pelicula6', 'director': 'Director3', 'año': 2021, 'precio_alquiler': 9.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula6'},
        {'nombre': 'Pelicula7', 'director': 'Director1', 'año': 2018, 'precio_alquiler': 7.99, 'disponible': False, 'sinopsis': 'Sinopsis de Pelicula7'},
        {'nombre': 'Pelicula8', 'director': 'Director2', 'año': 2019, 'precio_alquiler': 8.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula8'},
        {'nombre': 'Pelicula9', 'director': 'Director3', 'año': 2020, 'precio_alquiler': 6.99, 'disponible': True, 'sinopsis': 'Sinopsis de Pelicula9'},
        {'nombre': 'Pelicula10', 'director': 'Director1', 'año': 2022, 'precio_alquiler': 11.99, 'disponible': False, 'sinopsis': 'Sinopsis de Pelicula10'},
    ]

    for pelicula_info in peliculas_data:
        nueva_pelicula = Peliculas(**pelicula_info)
        db.session.add(nueva_pelicula)

    # Inserciones en la tabla Users
    users_data = [
        {'nombre': 'Usuario1', 'email': 'usuario1@example.com', 'password_k': 'contraseña1'},
        {'nombre': 'Usuario2', 'email': 'usuario2@example.com', 'password_k': 'contraseña2'},
    ]

    for user_info in users_data:
        nuevo_usuario = Users(**user_info)
        db.session.add(nuevo_usuario)

    # Guardar cambios en la base de datos
    db.session.commit()

    return 'Base de datos inicializada con datos de ejemplo.'


if __name__ == '__main__':
    app.run(debug=True)