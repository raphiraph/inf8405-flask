import urllib.parse
import json
from flask import Flask, request, jsonify
import flask.json
import decimal
from flask_sqlalchemy import SQLAlchemy

class MyJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        return super(MyJSONEncoder, self).default(obj)

# Configure Database URI:
params = urllib.parse.quote_plus("DRIVER={ODBC Driver 13 for SQL Server};SERVER=inf8405.database.windows.net;DATABASE=Projet;UID=inf8405;PWD=ProjetMobile1")

# Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mssql+pyodbc:///?odbc_connect=%s" % params
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json_encoder = MyJSONEncoder

db = SQLAlchemy(app)

# --------------------------------------------------------------- GET --------------------------------------------------------------- #

@app.route('/get-all-parties', methods=['GET'])
def get_all_parties():
    data = []
    query = db.session.execute("select * from Parties").fetchall()
    db.session.close()
    for row in query:
        json_row = {'id': row.id, 'name': row.name, 'longitude': row.longitude, 'latitude': row.latitude, 'decibels': row.decibels}
        data.append(json_row)
    return jsonify(data)

@app.route('/get-requested-songs', methods=['GET'])
def get_requested_songs():
    data = []
    party_name = request.args.get("party_name")
    query = db.session.execute("select * from RequestedSongs where party = '{}' order by RequestedSongs.position asc".format(party_name)).fetchall()
    db.session.close()
    for row in query:
        json_row = {'position': row.position, 'name': row.name, 'artist': row.artist, 'party': row.party}
        data.append(json_row)
    return jsonify(data)

@app.route('/get-available-songs', methods=['GET'])
def get_available_songs():
    data = []
    party_name = request.args.get("party_name")
    query = db.session.execute("select * from AvailableSongs where party = '{}'".format(party_name)).fetchall()
    db.session.close()
    for row in query:
        json_row = {'name': row.name, 'artist': row.artist, 'party': row.party}
        data.append(json_row)
    return jsonify(data)

# --------------------------------------------------------------- POST --------------------------------------------------------------- #

@app.route('/post-party', methods=['GET', 'POST'])
def post_party():
    name = request.args.get("party_name")
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")
    decibels = request.args.get("decibels")
    available_songs = json.loads(request.args.get("available_songs"))
    db.session.execute("insert into Parties(name,longitude,latitude,decibels) values('{}',{},{},{})".format(name, longitude, latitude, decibels))
    for song in available_songs:
        db.session.execute("insert into AvailableSongs(name,artist,party) values('{}','{}','{}')".format(song["name"], song["artist"], name))
    db.session.commit()
    db.session.close()
    return "Success"

@app.route('/post-song-request', methods=['GET', 'POST'])
def post_song_request():
    song_name = request.args.get("song_name")
    artist = request.args.get("artist")
    party_name = request.args.get("party_name")
    db.session.execute("insert into RequestedSongs(name,artist,party) values('{}','{}','{}')".format(song_name, artist, party_name))
    db.session.commit()
    db.session.close()
    return "Success"

# --------------------------------------------------------------- DELETE --------------------------------------------------------------- #

@app.route('/delete-song-request', methods=['GET', "DELETE"])
def delete_song_request():
    song_name = request.args.get("song_name")
    party_name = request.args.get("party_name")
    db.session.execute(
        "delete from RequestedSongs where RequestedSongs.name = '{}' and RequestedSongs.party = '{}'".format(song_name, party_name))
    db.session.commit()
    db.session.close()
    return "Success"

@app.route('/delete-all-song-requests', methods=['GET', "DELETE"])
def delete_all_song_requests():
    party_name = request.args.get("party_name")
    db.session.execute("delete from RequestedSongs where RequestedSongs.party = '{}'".format(party_name))
    db.session.commit()
    db.session.close()
    return "Success"

@app.route('/delete-available-song', methods=['GET', "DELETE"])
def delete_available_song():
    song_name = request.args.get("song_name")
    party_name = request.args.get("party_name")
    db.session.execute("delete from AvailableSongs where AvailableSongs.name = '{}' and AvailableSongs.party = '{}'".format(song_name, party_name))
    db.session.commit()
    db.session.close()
    return "Success"

@app.route('/delete-all-available-songs', methods=['GET', "DELETE"])
def delete_all_available_songs():
    party_name = request.args.get("party_name")
    db.session.execute("delete from AvailableSongs where AvailableSongs.party = '{}'".format(party_name))
    db.session.commit()
    db.session.close()
    return "Success"

@app.route('/delete-party', methods=['GET', "DELETE"])
def delete_party():
    party_name = request.args.get("party_name")
    db.session.execute("delete from Parties where Parties.name = '{}'".format(party_name))
    db.session.commit()
    db.session.close()
    return "Success"

# --------------------------------------------------------------- DB --------------------------------------------------------------- #

def make_bd():
    db.session.execute('CREATE TABLE RequestedSongs ('
                   'position int IDENTITY(1,1),'
                   'name varchar(100) NOT NULL,'
                   'artist varchar(100) NOT NULL,'
                   'party varchar(100) NOT NULL,'
                   'PRIMARY KEY (name, party)'
                   ');'
                   'CREATE TABLE AvailableSongs ('
                   'name varchar(100) NOT NULL,'
                   'artist varchar(100) NOT NULL,'
                   'party varchar(100) NOT NULL,'
                   'PRIMARY KEY (name, party)'
                   ');'
                   'CREATE TABLE Parties ('
                   'id int IDENTITY(1,1),'
                   'name varchar(100) NOT NULL UNIQUE,'
                   'longitude decimal(9,6) NOT NULL,'
                   'latitude decimal(9,6) NOT NULL,'
                   'decibels int NOT NULL,'
                   'PRIMARY KEY (id)'
                   ');'
                   'ALTER TABLE AvailableSongs ADD CONSTRAINT fk_available_songs_party FOREIGN KEY (party) REFERENCES Parties(name);'
                   'ALTER TABLE RequestedSongs ADD CONSTRAINT fk_requested_songs_party FOREIGN KEY (party) REFERENCES Parties(name);'
                   )
    db.session.commit()
    db.session.close()


def delete_and_remake_bd():
    db.session.execute('ALTER TABLE Availablesongs DROP CONSTRAINT fk_available_songs_party;'
                   'ALTER TABLE RequestedSongs DROP CONSTRAINT fk_requested_songs_party;'
                   'DROP TABLE Parties;'
                   'DROP TABLE RequestedSongs;'
                   'DROP TABLE AvailableSongs;'
                   'CREATE TABLE RequestedSongs ('
                   'position int IDENTITY(1,1),'
                   'name varchar(100) NOT NULL,'
                   'artist varchar(100) NOT NULL,'
                   'party varchar(100) NOT NULL,'
                   'PRIMARY KEY (name, party)'
                   ');'
                   'CREATE TABLE AvailableSongs ('
                   'name varchar(100) NOT NULL,'
                   'artist varchar(100) NOT NULL,'
                   'party varchar(100) NOT NULL,'
                   'PRIMARY KEY (name, party)'
                   ');'
                   'CREATE TABLE Parties ('
                   'id int IDENTITY(1,1),'
                   'name varchar(100) NOT NULL UNIQUE,'
                   'longitude decimal(9,6) NOT NULL,'
                   'latitude decimal(9,6) NOT NULL,'
                   'decibels int NOT NULL,'
                   'PRIMARY KEY (id)'
                   ');'
                   'ALTER TABLE AvailableSongs ADD CONSTRAINT fk_available_songs_party FOREIGN KEY (party) REFERENCES Parties(name);'
                   'ALTER TABLE RequestedSongs ADD CONSTRAINT fk_requested_songs_party FOREIGN KEY (party) REFERENCES Parties(name);'
                   )
    db.session.commit()
    db.session.close()

if __name__ == '__main__':
    app.run()

# delete_and_remake_bd()
# post_party("Party", 173.987654321, 173.987654321, 120, [{"name":"yeah", "artist":"yo"},{"name":"yeah 2", "artist":"yo"},{"name":"yeah 3", "artist":"yo"}])
# print(get_all_parties())
# print(get_available_songs("Party"))
# post_song_request("yeah", "yo", "Party")
# print(get_requested_songs("Party"))
# delete_all_song_requests("Party")
# print(get_requested_songs("Party"))
# delete_all_available_songs("Party")
# print(get_available_songs("Party"))
# delete_party("Party")
# print(get_all_parties())

# print(get_requested_songs(connection, "Party"))
# print(get_available_songs(connection, "Party"))
# make_bd(connection)

# ?party_name=Party&longitude=173.987654321&latitude=173.987654321&decibels=120&available_songs=[{"name":"yeah",%20"artist":"yo"},{"name":"yeah%202",%20"artist":"yo"},{"name":"yeah%203",%20"artist":"yo"}]