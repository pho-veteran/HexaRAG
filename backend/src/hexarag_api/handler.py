from mangum import Mangum

from hexarag_api.main import app

handler = Mangum(app)
