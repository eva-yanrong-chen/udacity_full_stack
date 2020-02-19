#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Helper.
#----------------------------------------------------------------------------#


def isPast(datetime):
    now = datetime.now()
    return datetime < now

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Show(db.Model):
    __tablename__ = 'show'

    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.now, primary_key=True)

    def __repr__(self):
        return f'<Show: Venue {self.venue_id} & Artist {self.artist_id} starts @ {self.start_time}>'

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    website = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String())
    artists = db.relationship('Artist', secondary="show",
                              backref=db.backref('venues'))

    def __repr__(self):
        return f'<Venue {self.id}: {self.name} @ {self.city}>'

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean, nullable=False)
    seeking_description = db.Column(db.String())

    def __repr__(self):
        return f'<Artist {self.id}: {self.name} @ {self.city}>'


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    #   num_shows should be aggregated based on number of upcoming shows per venue.
    data = []

    cities = db.session.query(Venue.city).group_by('city').all()
    for city in cities:
        exampleVenue = Venue.query.filter_by(city=city).first()
        cityDic = {"city": exampleVenue.city,
            "state": exampleVenue.state,
            "venues": []
        }
        venues = Venue.query.filter_by(city = city).all()
        for venue in venues:
            venueDic = {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": Show.query.filter_by(venue_id=venue.id).filter(Show.start_time >= datetime.now()).count()
            }
            cityDic["venues"].append(venueDic)
        data.append(cityDic)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    response = {
        "count": 0,
        "data": []
    }
    search_term = request.form['search_term']
    venues = db.session.query(Venue).filter(Venue.name.ilike('%' + search_term + '%')).all()
    for venue in venues:
        venueDic = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": Show.query.filter_by(venue_id=venue.id).count()
        }
        response['data'].append(venueDic)
        response['count']+=1
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    data = []
    for venue in Venue.query.all():
        venueDic = {
            "id": venue.id,
            "name": venue.name,
            "genres": venue.genres,
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": Show.query.filter_by(venue_id=venue.id).filter(Show.start_time < datetime.now()).count(),
            "upcoming_shows_count": Show.query.filter_by(venue_id=venue.id).filter(Show.start_time >= datetime.now()).count(),
        }
        print(venueDic["genres"])
        shows = Show.query.filter_by(venue_id=venue.id).all()
        for show in shows:
            artist = Artist.query.filter_by(id=show.artist_id).one()
            showDic = {
                "artist_id": show.artist_id,
                "artist_name": artist.name,
                "artist_image_link": artist.image_link,
                "start_time": format_datetime(show.start_time.strftime("%Y-%m-%d, %H:%M:%S"))
            }
            if isPast(show.start_time):
                venueDic["past_shows"].append(showDic)
            else:
                venueDic["upcoming_shows"].append(showDic)
        data.append(venueDic)

    data = list(filter(lambda d: d['id'] ==
                       venue_id, data))[0]
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm(request.form)
    error = False

    if form.validate():
        try:
            newVenue = Venue(
                name=request.form['name'],
                city=request.form['city'],
                state=request.form['state'],
                address=request.form['address'],
                phone=request.form['phone'],
                genres=request.form.getlist('genres'),
                image_link=request.form['image_link'],
                facebook_link=request.form['facebook_link'],
                website=request.form['website'],
                seeking_talent=request.form['seeking_talent'] == 'Yes',
                seeking_description=request.form['seeking_description']
            )
            db.session.add(newVenue)
            db.session.commit()
            flash('Venue ' + request.form['name'] + ' has been created!')
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash('An ' + e + ' error occurred. Venue ' +
                  data.name + ' could not be listed.')
            return render_template('forms/new_venue.html', form=form)
        else:
            return render_template('pages/home.html')
    else:
        flash('Venue' + request.form['name'] +
                                     ' cannot be list. Please double check the fields.')
        return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.filter_by(id=venue_id).one()
        db.session.delete(venue)
        db.session.commit()
    except:
        db.session.rollback()       
    finally:
        db.session.close()

    # TODO: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage

    print("DELETE")
    return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = []
    artists = Artist.query.all()
    for artist in artists:
        artistDic = {"id": artist.id, "name": artist.name}
        data.append(artistDic)
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    response = {
        "count": 0,
        "data": []
    }
    search_term = request.form['search_term']
    artists = db.session.query(Artist).filter(
        Artist.name.ilike('%' + search_term + '%')).all()
    for artist in artists:
        artistDic = {
            "id": artist.id,
            "name": artist.name,
            "num_upcoming_shows": Show.query.filter_by(artist_id=artist.id).filter(Show.start_time >= datetime.now()).count()
        }
        response['data'].append(artistDic)
        response['count'] += 1
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
   
    data=[]

    artists = Artist.query.all()

    for artist in artists:
        artistDic = {
            "id": artist.id,
            "name": artist.name,
            "genres": artist.genres,
            "city": artist.city,
            "state": artist.state,
            "phone": artist.phone,
            "seeking_venue": artist.seeking_venue,
            "image_link": artist.image_link,
            "past_shows": [],
            "upcoming_shows": [],
            "past_shows_count": Show.query.filter_by(artist_id=artist.id).filter(Show.start_time < datetime.now()).count(),
            "upcoming_shows_count": Show.query.filter_by(artist_id=artist.id).filter(Show.start_time >= datetime.now()).count(),
        }
        #BUG artist genres are printing weird
        shows = Show.query.filter_by(artist_id=artist.id).all()
        for show in shows:
            venue = Venue.query.filter_by(id=show.venue_id).one()
            showDic = {
                "venue_id": show.venue_id,
                "venue_name": venue.name,
                "venue_image_link": venue.image_link,
                "start_time": format_datetime(show.start_time.strftime("%Y-%m-%d, %H:%M:%S"))
            }
            if isPast(show.start_time):
                artistDic["past_shows"].append(showDic)
            else:
                artistDic["upcoming_shows"].append(showDic)
        data.append(artistDic)
    data = list(filter(lambda d: d['id'] ==
                       artist_id, data))[0]
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = db.session.query(Artist).filter_by(id=artist_id).one()
    # BUG can't populate select fields with default values
    return render_template('forms/edit_artist.html', form=form, artist=artist)
    # TODO add remaining fields to the form and update them

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    form = ArtistForm()
    try:
        artist = db.session.query(Artist).filter_by(id=artist_id).one()
        artist.name = request.form['name'],
        artist.city = request.form['city'],
        artist.state = request.form['state'],
        artist.phone = request.form['phone'],
        artist.genres = request.form.getlist('genres'),
        artist.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).one()
    # BUG can't populate select fields with default values
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes

    try:
        venue = db.session.query(Venue).filter_by(id=venue_id).one()
        venue.name = request.form['name'],
        venue.city = request.form['city'],
        venue.state = request.form['state'],
        venue.phone = request.form['phone'],
        venue.genres = request.form.getlist('genres'),
        venue.facebook_link = request.form['facebook_link']
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm(request.form)
    error = False

    if form.validate():
        try:
            newArtist = Artist(
                name=request.form['name'],
                city=request.form['city'],
                state=request.form['state'],
                phone=request.form['phone'],
                genres=request.form.getlist('genres'),
                image_link=request.form['image_link'],
                facebook_link=request.form['facebook_link'],
                website=request.form['website'],
                seeking_venue=request.form['seeking_venue'] == 'Yes',
                seeking_description=request.form['seeking_description']
            )
            db.session.add(newArtist)
            db.session.commit()
            flash('Artist ' + request.form['name'] + ' has been created!')
        except RuntimeError as e:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash('An ' + e + ' error occurred. Venue ' +
                  data.name + ' could not be listed.')
            return render_template('forms/new_artist.html', form=form)
        else:
            return render_template('pages/home.html')
    else:
        print(form.errors)
        flash('Artist ' + request.form['name'] +
                                     ' cannot be listed. Please double check the fields.')
        return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    #       num_shows should be aggregated based on number of upcoming shows per venue.
    data = []
    shows = Show.query.all()
    for show in shows:
        showDic = {
            "venue_id": show.venue_id,
            "venue_name": Venue.query.filter_by(id = show.venue_id).first().name,
            "artist_id": show.artist_id,
            "artist_image_link": Artist.query.filter_by(id = show.artist_id).first().image_link,
            "start_time": format_datetime(show.start_time.strftime("%Y-%m-%d, %H:%M:%S"))
        }
        data.append(showDic)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm(request.form)
    error = False

    if form.validate():
        try:
            start_time_string = request.form['start_time']
            newShow = Show(
                venue_id = request.form['venue_id'],
                artist_id = request.form['artist_id'],
                start_time=datetime.strptime(
                    start_time_string, '%Y-%m-%d %H:%M:%S')
            )
            db.session.add(newShow)
            db.session.commit()
            flash('Show was successfully listed!')
        except RuntimeError as e:
            print(e)
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash('An error occurred. Show could not be listed.')
            return render_template('forms/new_show.html', form=form)
        else:
            return render_template('pages/home.html')
    else:
        flash('Artist or Venue id does not exist. Please check all the fields.')
        return render_template('forms/new_show.html', form=form)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''


