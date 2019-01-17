from flask_restful import Resource, reqparse

class BlockAPI(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
    
    def get(self):
        return {"message": "Get Block!"}

    def post(self):
        self.parser.add_argument('message', type=str)
        args = self.parser.parse_args()

        return {"message": "Post {}!".format(args['message'])}