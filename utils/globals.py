import os


function_details = {
    'document_builder': {
        'name': 'Document Builder',
        'description': 'Generate a client-ready document from a template and reference ID.',
        'endpoint': 'document_builder.build_document',
    },
    'transaction_lookup': {
        'name': 'Transaction Lookup',
        'description': 'Search records by reference IDs and export results to Excel.',
        'endpoint': 'transaction_lookup.lookup',
    },
}


process_states = {}
temp_dir = os.path.join('data', 'temp')
