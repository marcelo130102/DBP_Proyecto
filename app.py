from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:marcelo@localhost/store'  # Cambia estos valores según tu configuración
db = SQLAlchemy(app)

class Peliculas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(255), nullable=False)
    director = db.Column(db.String(255))
    año = db.Column(db.Integer)
    precio_alquiler = db.Column(db.Float)
    disponible = db.Column(db.Boolean)
    sinopsis = db.Column(db.Text)

@app.route("/")
def main():
    peliculas = Peliculas.query.all()
    peliculas_lista = []
    return render_template('index.html', peliculas=peliculas)

@app.route('/pelicula/<int:pelicula_id>')
def ver_pelicula(pelicula_id):
    pelicula = Peliculas.query.get(pelicula_id)
    return render_template('detalles.html', pelicula=pelicula)


@app.route('/registro')
def registro():
    return render_template('registro.html')

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

    return jsonify({'mensaje': 'Pelicula agregada correctamente'})

if __name__ == '__main__':
    app.run(debug=True)