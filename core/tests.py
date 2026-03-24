from django.test import TestCase

# Create your tests here.
class SearchTests(TestCase):
    def check_empty_query():
        "Should redirect to index"
        pass

    def check_empty_type():
        "Should redirect to index"
        pass

    def check_empty_order():
        "Should be fine"
        pass

    def check_missing_query():
        "Should redirect to index"
        pass

    def check_missing_type():
        "Should redirect to index"
        pass

    def check_missing_order():
        "Should be fine"
        pass

    def check_invalid_type():
        "Should redirect to index"
        pass

    def check_invalid_order():
        "Should be fine (uses default order)"
        pass

    def check_no_result():
        "Should show default message for no search results."
        pass

    def check_for_results():
        "Should return search results."
        pass
