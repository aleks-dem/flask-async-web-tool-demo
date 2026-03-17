import os
import random
import time
import hashlib
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from celery_app import celery

import utils.globals as g
from utils.redis_state_repository import get_process_state, set_process_state
from utils.observability import set_request_context, reset_request_context, observe_task


logger = logging.getLogger(__name__)


def update_state(
    user_id,
    function_key,
    status=None,
    progress=None,
    error=None,
    message=None,
    results=None,
    file_url=None,
    timestamp=None,
):
    state = get_process_state(user_id, function_key) or {}
    if status is not None:
        state['status'] = status
    if progress is not None:
        state['progress'] = progress
    if error is not None:
        state['error'] = error
    if message is not None:
        state['message'] = message
    if results is not None:
        state['results'] = results
    if file_url is not None:
        state['file_url'] = file_url
    if timestamp is not None:
        state['timestamp'] = timestamp
    set_process_state(user_id, function_key, state)


def save_df_with_autowidth(df, file_path):
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1', index=False)

    worksheet = writer.sheets['Sheet1']
    for index, column in enumerate(df.columns):
        max_length = max(df[column].astype(str).map(len).max(), len(column))
        worksheet.set_column(index, index, max_length + 2)

    writer.close()


def generate_mock_row(reference_id, start_date, end_date):
    seed = int.from_bytes(hashlib.sha256(str(reference_id).encode('utf-8')).digest()[:4], 'big')
    rng = random.Random(seed)

    dt_start = datetime.strptime(start_date, '%Y-%m-%d')
    dt_end = datetime.strptime(end_date, '%Y-%m-%d')
    span_days = max(0, (dt_end - dt_start).days)

    created_dt = dt_start + timedelta(days=rng.randint(0, span_days if span_days > 0 else 0))
    updated_dt = created_dt + timedelta(hours=rng.randint(1, 48))

    amount = round(rng.uniform(10, 500), 2)
    fee = round(amount * rng.uniform(0.01, 0.05), 2)

    workspace = 'Workspace A' if rng.randint(0, 1) == 0 else 'Workspace B'
    currency = 'USD' if workspace == 'Workspace A' else 'EUR'

    return {
        'input_reference': reference_id,
        'workspace': workspace,
        'record_id': f'REC-{rng.randint(100000, 999999)}',
        'created_at': created_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'updated_at': updated_dt.strftime('%Y-%m-%d %H:%M:%S'),
        'processing_route': rng.choice(['api', 'batch', 'manual_review']),
        'record_status': rng.choice(['approved', 'pending', 'review']),
        'user_id': f'U{rng.randint(10000, 99999)}',
        'user_registered_at': (created_dt - timedelta(days=rng.randint(30, 900))).strftime('%Y-%m-%d'),
        'currency': currency,
        'amount': amount,
        'amount_usd': amount if currency == 'USD' else round(amount * 1.08, 2),
        'fee': fee,
        'fee_usd': fee if currency == 'USD' else round(fee * 1.08, 2),
        'masked_instrument': f"{rng.randint(4000, 5999)} **** **** {rng.randint(1000, 9999)}",
        'source_name': rng.choice(['SourceAlpha', 'SourceBeta', 'SourceGamma']),
        'payment_method': rng.choice(['card', 'wallet', 'bank_transfer']),
        'source_reference': f'SR-{rng.randint(1000000, 9999999)}',
        'merchant_account': f'MA-{rng.randint(100, 999)}',
        'gateway_route': rng.choice(['route_primary', 'route_backup']),
        'gateway_account': f'GA-{rng.randint(1000, 9999)}',
        'source_code': f'SC-{rng.randint(10, 99)}',
        'tenant_account': f'TA-{rng.randint(100, 999)}',
        'external_reference': f'EXT-{rng.randint(100000, 999999)}',
        'external_payment_id': f'PAY-{rng.randint(10000000, 99999999)}',
    }


@celery.task
def transaction_lookup_process(user_id, function_key, start_date, end_date, reference_ids):
    task_started_at = time.perf_counter()
    task_id = getattr(transaction_lookup_process.request, 'id', None)
    ctx_tokens = set_request_context(
        request_id=f'celery-{task_id}' if task_id else 'celery-unknown',
        user_id=str(user_id),
    )
    observe_task('transaction_lookup', 'started')
    logger.info(
        'task_started',
        extra={
            'event': 'task_started',
            'function_key': function_key,
            'task_id': task_id or '-',
        },
    )
    try:
        update_state(user_id, function_key, status='processing', progress=0, error=None)

        total_ids = len(reference_ids)
        if total_ids == 0:
            duration = max(0.0, time.perf_counter() - task_started_at)
            observe_task('transaction_lookup', 'no_data', duration_seconds=duration)
            update_state(
                user_id,
                function_key,
                status='no_data',
                progress=100,
                timestamp=time.time(),
                message='No reference IDs were provided.',
            )
            logger.info(
                'task_completed_no_data',
                extra={
                    'event': 'task_completed_no_data',
                    'function_key': function_key,
                    'task_id': task_id or '-',
                    'duration_ms': round(duration * 1000, 2),
                },
            )
            return

        final_df = pd.DataFrame()

        for index, ref_id in enumerate(reference_ids, start=1):
            row = generate_mock_row(ref_id, start_date, end_date)
            df_part = pd.DataFrame([row])

            final_df = pd.concat([final_df, df_part], ignore_index=True)

            progress_percent = int(index / total_ids * 100)
            update_state(user_id, function_key, status='processing', progress=progress_percent)
            time.sleep(0.05)

        if final_df.empty:
            duration = max(0.0, time.perf_counter() - task_started_at)
            observe_task('transaction_lookup', 'no_data', duration_seconds=duration)
            update_state(
                user_id,
                function_key,
                status='no_data',
                progress=100,
                message='No data found.',
                timestamp=time.time(),
            )
            logger.info(
                'task_completed_no_data',
                extra={
                    'event': 'task_completed_no_data',
                    'function_key': function_key,
                    'task_id': task_id or '-',
                    'duration_ms': round(duration * 1000, 2),
                },
            )
            return

        for column in final_df.columns:
            if pd.api.types.is_datetime64_dtype(final_df[column]):
                final_df[column] = final_df[column].astype(str)

        now_str = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        filename = f'{now_str}_transaction_lookup_result.xlsx'
        file_path = os.path.join(g.temp_dir, filename)

        save_df_with_autowidth(final_df, file_path)
        results_list = final_df.replace({np.nan: ''}).to_dict(orient='records')

        update_state(
            user_id,
            function_key,
            status='completed',
            progress=100,
            results=results_list,
            file_url=f"download/{function_key}/{os.path.basename(file_path)}",
            timestamp=time.time(),
        )
        duration = max(0.0, time.perf_counter() - task_started_at)
        observe_task('transaction_lookup', 'completed', duration_seconds=duration)
        logger.info(
            'task_completed',
            extra={
                'event': 'task_completed',
                'function_key': function_key,
                'task_id': task_id or '-',
                'duration_ms': round(duration * 1000, 2),
            },
        )
    except Exception as exc:
        duration = max(0.0, time.perf_counter() - task_started_at)
        observe_task('transaction_lookup', 'error', duration_seconds=duration)
        logger.exception(
            'task_failed',
            extra={
                'event': 'task_failed',
                'function_key': function_key,
                'task_id': task_id or '-',
                'duration_ms': round(duration * 1000, 2),
            },
        )
        update_state(user_id, function_key, status='error', progress=0, error=str(exc))
    finally:
        reset_request_context(ctx_tokens)
