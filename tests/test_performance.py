# Copyright (c) 2025 [KTISEOS NYX / 0FTH3N1GHT / EARTH & DUSK MEDIA]
# SPDX-License-Identifier: MIT

"""Performance and timing tests for metadata parser"""

import time
from pathlib import Path

import pytest

from dataset_tools.metadata_parser import parse_metadata

# Get the directory of the current test file
TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "data"

# Get a list of all files in the data directory
all_files = [f for f in DATA_DIR.iterdir() if f.is_file()]


def test_individual_file_parse_speed():
    """Test that individual files parse within reasonable time limits."""
    slow_files = []

    for file_path in all_files:
        if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".json"]:
            start_time = time.time()
            try:
                metadata = parse_metadata(str(file_path))
                parse_time = time.time() - start_time

                # Individual file should parse within 5 seconds (reasonable limit)
                if parse_time > 5.0:
                    slow_files.append((file_path.name, parse_time))

            except Exception as e:
                # Track failed parses for analysis
                pytest.fail(f"File {file_path.name} failed to parse: {e}")

    if slow_files:
        slow_list = "\n".join([f"  {name}: {time:.2f}s" for name, time in slow_files])
        pytest.fail(f"Files took too long to parse:\n{slow_list}")


def test_batch_parsing_performance():
    """Test parsing multiple files in sequence for overall performance."""
    start_time = time.time()
    successful_parses = 0
    total_files = 0

    for file_path in all_files:
        if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".json"]:
            total_files += 1
            try:
                metadata = parse_metadata(str(file_path))
                if metadata:
                    successful_parses += 1
            except Exception:
                # Don't fail the test for individual file errors in batch test
                pass

    total_time = time.time() - start_time

    # Performance assertions
    assert total_files > 0, "No test files found"
    assert successful_parses > 0, "No files were successfully parsed"

    avg_time_per_file = total_time / total_files
    success_rate = successful_parses / total_files

    print("\n📊 Batch Performance Results:")
    print(f"   Total files tested: {total_files}")
    print(f"   Successful parses: {successful_parses}")
    print(f"   Success rate: {success_rate:.1%}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per file: {avg_time_per_file:.3f}s")

    # Reasonable performance expectations
    assert avg_time_per_file < 2.0, f"Average parse time too slow: {avg_time_per_file:.3f}s"
    assert success_rate > 0.8, f"Success rate too low: {success_rate:.1%}"


@pytest.mark.parametrize("file_path", all_files[:5])  # Test first 5 files for detailed timing
def test_detailed_timing_breakdown(file_path):
    """Test detailed timing breakdown for specific files."""
    if file_path.suffix.lower() not in [".png", ".jpg", ".jpeg", ".json"]:
        pytest.skip(f"Skipping non-target file: {file_path}")

    # Warm-up run (cache any imports/initialization)
    try:
        parse_metadata(str(file_path))
    except:
        pass  # Ignore errors in warm-up

    # Timed runs
    times = []
    for i in range(3):  # Run 3 times for more reliable timing
        start_time = time.time()
        try:
            metadata = parse_metadata(str(file_path))
            parse_time = time.time() - start_time
            times.append(parse_time)
            assert metadata is not None, "Metadata should not be None"
        except Exception as e:
            pytest.fail(f"Parse failed on run {i + 1}: {e}")

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    print(f"\n⏱️  Timing for {file_path.name}:")
    print(f"   File size: {file_size_mb:.2f}MB")
    print(f"   Min time: {min_time:.3f}s")
    print(f"   Avg time: {avg_time:.3f}s")
    print(f"   Max time: {max_time:.3f}s")
    print(f"   Speed: {file_size_mb / avg_time:.2f}MB/s")

    # Performance assertions
    assert avg_time < 3.0, f"Average time too slow: {avg_time:.3f}s"
    assert max_time < 5.0, f"Maximum time too slow: {max_time:.3f}s"


def test_memory_usage_stability():
    """Test that parsing multiple files doesn't cause memory leaks."""
    import os

    import psutil

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / (1024 * 1024)  # MB

    # Parse several files multiple times
    test_files = [f for f in all_files if f.suffix.lower() in [".png", ".jpg", ".jpeg"]][:3]

    for iteration in range(5):  # 5 iterations
        for file_path in test_files:
            try:
                metadata = parse_metadata(str(file_path))
            except:
                pass  # Ignore parse errors for memory test

    final_memory = process.memory_info().rss / (1024 * 1024)  # MB
    memory_increase = final_memory - initial_memory

    print("\n🧠 Memory Usage:")
    print(f"   Initial memory: {initial_memory:.1f}MB")
    print(f"   Final memory: {final_memory:.1f}MB")
    print(f"   Memory increase: {memory_increase:.1f}MB")

    # Should not leak more than 50MB during testing
    assert memory_increase < 50, f"Possible memory leak: {memory_increase:.1f}MB increase"


def test_large_file_handling():
    """Test performance with the largest files in the test dataset."""
    large_files = []

    for file_path in all_files:
        if file_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".json"]:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            large_files.append((file_path, size_mb))

    # Sort by size and take the largest files
    large_files.sort(key=lambda x: x[1], reverse=True)
    largest_files = large_files[:3]  # Test 3 largest files

    if not largest_files:
        pytest.skip("No large files found in test dataset")

    for file_path, size_mb in largest_files:
        start_time = time.time()
        try:
            metadata = parse_metadata(str(file_path))
            parse_time = time.time() - start_time
            throughput = size_mb / parse_time if parse_time > 0 else 0

            print(f"📁 {file_path.name}: {size_mb:.2f}MB in {parse_time:.2f}s ({throughput:.1f}MB/s)")

            # Large files should still parse within reasonable time
            assert parse_time < 10.0, f"Large file {file_path.name} took too long: {parse_time:.2f}s"
            assert metadata is not None, f"Large file {file_path.name} returned no metadata"

        except Exception as e:
            pytest.fail(f"Large file {file_path.name} failed to parse: {e}")


def test_concurrent_parsing_safety():
    """Test that the parser is thread-safe for concurrent operations."""
    import queue
    import threading

    test_files = [f for f in all_files if f.suffix.lower() in [".png", ".jpg", ".jpeg"]][:5]
    if not test_files:
        pytest.skip("No test files available for concurrent testing")

    results_queue = queue.Queue()
    errors_queue = queue.Queue()

    def parse_worker(file_path):
        try:
            start_time = time.time()
            metadata = parse_metadata(str(file_path))
            parse_time = time.time() - start_time
            results_queue.put((file_path.name, parse_time, metadata is not None))
        except Exception as e:
            errors_queue.put((file_path.name, str(e)))

    # Start multiple threads parsing different files
    threads = []
    for file_path in test_files:
        thread = threading.Thread(target=parse_worker, args=(file_path,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join(timeout=30)  # 30 second timeout per thread
        assert not thread.is_alive(), "Thread did not complete in time"

    # Check results
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())

    errors = []
    while not errors_queue.empty():
        errors.append(errors_queue.get())

    print("\n🧵 Concurrent Results:")
    for name, parse_time, success in results:
        print(f"   ✅ {name}: {parse_time:.3f}s")

    for name, error in errors:
        print(f"   ❌ {name}: {error}")

    # At least some files should parse successfully
    assert len(results) > 0, "No files parsed successfully in concurrent test"
    assert len(errors) < len(test_files), "Too many files failed in concurrent test"
