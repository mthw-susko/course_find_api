from coursefind import app
from flask import json, jsonify, Blueprint, request
from flask_cors import cross_origin
from coursefind.models import Course

main = Blueprint("main", __name__)


@main.route("/")
@cross_origin()
def home():
    return jsonify(
        {
            "routes": [
                {
                    "/course": {
                        "url args": "semester code",
                        "description": "return all courses for a given semester",
                    }
                },
                {
                    "/course/<COURSE_CODE>": {
                        "url args": "semester code",
                        "description": "return information about given course code",
                    }
                },
            ]
        }
    )


@main.route("/course")
@cross_origin()
def all_courses():
    courses = Course.query.with_entities(Course.code).distinct()
    codes = [course.code for course in courses]
    return jsonify({"course_codes": codes})


@main.route("/course/<string:code>")
@cross_origin()
def get_course(code):
    course = Course.query.filter_by(code=code).first()

    if not course:
        return jsonify({"error": "class not found"}), 404

    course = course.asdict()
    return jsonify({"course_info": course})
