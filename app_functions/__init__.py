from flask import Blueprint

document_builder_bp = Blueprint('document_builder', __name__, url_prefix='/document_builder')
transaction_lookup_bp = Blueprint('transaction_lookup', __name__, url_prefix='/transaction_lookup')
