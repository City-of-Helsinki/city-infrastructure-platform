# {
#   "status": 400,
#   "error": {
#     "code": "VALIDATION_ERROR",
#     "message": "Validation error",
#     "details": {
#       "fields": {
#         "name": [
#           "This field is required"
#         ],
#         "age": [
#           "Value must be greater than 0"
#         ]
#       }
#     }
#   }
# }

# {
#   "status": 404,
#   "error": {
#     "code": "OBJECT_NOT_FOUND",
#     "message": "Object not found",
#     "details": {
#       "id": "5c08edc9-4450-409c-895a-cadb6ac617c3"
#     }
#   }
# }

class CityinfraException(Exception):
    message = "Unknown error"

class CityinfraObjectNotFound(Exception):
    message = "Object not found"
    def __init__(self, code=None, params=None):
