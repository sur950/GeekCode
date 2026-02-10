# Legacy data processor module - needs refactoring
# This is sample input for Task 1: Python Module Refactoring

import json
import csv
import time

BATCH_SIZE = 100
TIMEOUT = 30.0
RETRY_COUNT = 3

def load_data(filepath):
    """Load data from file."""
    if filepath.endswith('.json'):
        with open(filepath, 'r') as f:
            return json.load(f)
    elif filepath.endswith('.csv'):
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        raise ValueError("Unsupported file format: %s" % filepath)

def validate_record(record):
    """Validate a single record."""
    if not record:
        return False
    if 'id' not in record:
        return False
    if 'name' not in record:
        return False
    return True

def transform_record(record):
    """Transform a single record."""
    result = {}
    result['id'] = str(record.get('id', ''))
    result['name'] = record.get('name', '').strip().title()
    result['email'] = record.get('email', '').lower()
    result['timestamp'] = time.time()
    return result

def process_batch(records):
    """Process a batch of records."""
    results = []
    for record in records:
        if validate_record(record):
            transformed = transform_record(record)
            results.append(transformed)
    return results

def process_data(data):
    """Main entry point - process all data."""
    all_results = []
    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        batch_results = process_batch(batch)
        all_results.extend(batch_results)
        print("Processed batch %d, total records: %d" % (i // BATCH_SIZE + 1, len(all_results)))
    return all_results

def save_results(results, filepath):
    """Save results to file."""
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    print("Saved %d records to %s" % (len(results), filepath))

def run_pipeline(input_path, output_path):
    """Run the full processing pipeline."""
    retries = 0
    while retries < RETRY_COUNT:
        try:
            data = load_data(input_path)
            results = process_data(data)
            save_results(results, output_path)
            return True
        except Exception as e:
            retries += 1
            print("Error: %s. Retry %d/%d" % (str(e), retries, RETRY_COUNT))
            time.sleep(TIMEOUT / 10)
    return False


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python data_processor.py <input> <output>")
        sys.exit(1)
    success = run_pipeline(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
