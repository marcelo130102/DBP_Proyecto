from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:marcelo@localhost/store'
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


if __name__ == '__main__':
    app.run(debug=True)