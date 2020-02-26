import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start = (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  
  '''
  Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  CORS(app)

  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers',
                           'Content-Type, Authorization')
      response.headers.add('Access-Control-Allow-Methods',
                           'Get, POST, PATCH, DELETE, OPTIONS')
      return response

  '''
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = {}
    for category in Category.query.order_by(Category.id).all():
      categories[category.format()['id']] = category.format()['type']

    if len(categories) == 0:
      abort(404)

    return jsonify({
        'success': True,
        'categories': categories,
        'total_categories': len(Category.query.all())
    })

  '''
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def get_questions():
    questions = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, questions)

    if len(current_questions) == 0:
      abort(404)

    categories = {}
    for category in Category.query.order_by(Category.id).all():
      categories[category.format()['id']] = category.format()['type']

    if len(categories) == 0:
      abort(404)
    
    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'categories': categories
    })

  '''
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.get(question_id).delete()
      return jsonify({
        'success': True,
        'deleted': question_id,
        'total_questions': len(Question.query.all())
        })
    except Exception as error:
      print("\nerror => {}\n".format(error))
      abort(422)

  '''
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  ''' 
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
    searchTerm = body.get('searchTerm', None)
    question = body.get('question', None)
    answer = body.get('answer', None)
    difficulty = body.get('difficulty', None)
    category = body.get('category', None)

    try:
      if searchTerm:
        questions = Question.query.filter(Question.question.ilike(f'%{searchTerm}%')).all()
        current_questions = paginate_questions(request, questions)

        return jsonify({
          'success': True,
          'questions': current_questions,
          'total_questions': len(current_questions)
        })

      else:
        newQuestion = Question(question, answer, difficulty, category)
        newQuestion.insert()

        return jsonify({
          'success': True,
          'question_created': newQuestion.format()
        })
    except Exception as error:
      print("\nerror => {}\n".format(error))
      abort(422)


  '''
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    questions = Question.query.filter_by(category=category_id).all()
    current_questions = paginate_questions(request, questions)

    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(current_questions)
    })

  '''
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''
  @app.route('/quizzes', methods=['POST'])
  def create_quiz():
    body = request.get_json()
    previous_questions = body.get('previous_questions')
    quiz_category = body.get('quiz_category')
    category_id = quiz_category['id']
    
    try:
      if category_id == 0:
        questions = Question.query.all()
      else:
        questions = Question.query.filter_by(category=category_id).all()
      
      if len(questions) == 0:
        abort(404)

      formatted_questions = [question.format() for question in questions]

      print('previous questions', previous_questions)

      possible_questions = []
      for q in formatted_questions:
        if q['id'] not in previous_questions:
          possible_questions.append(q)

      if len(possible_questions) == 0:
        return jsonify({
          'success': True
        })

      next_question = random.choice(possible_questions)

      previous_questions.append(next_question)

      return jsonify({
        'success': True,
        'question': next_question,
        'previous_questions': previous_questions,
        'quizCategory': quiz_category
      })
    
    except Exception as error:
      print("\nerror => {}\n".format(error))
      abort(422)

  '''
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422
  
  return app

    
