from flask import Blueprint
from flask_restful import Api
from resources.Block import BlockAPI

blueprint = Blueprint('api', __name__)
api = Api(blueprint)

api.add_resource(BlockAPI, '/')