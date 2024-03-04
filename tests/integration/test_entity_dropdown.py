"""
Test that our entity dropdown does what we expect

This may end up being re-named/combined with tests of our other drop-downs,
depending on how much duplication there is.
"""
# Tests to write:
# - test that the entity dropdown does what we want
#   - update entity dropdown to a new value
#   - check
#     - source-scenario dropdown updates
#       - should update to reflect only the source-scenarios in the new entity
#     - entity figure updates
#       - fairly self-explanatory
#     - category figure updates
#       - should update to reflect only the categories in the new entity
#     - main figure updates
#       - should update to reflect only the source-scenarios in the new entity
#   - inputs for the test
#     - dataset (we'll need to create)
#   - cases
#     - nothing needs to change in source-scenario dropdown
#     - nothing needs to change in main figure
#     - things need to change in source-scenario dropdown
#     - things need to change in main figure
#     - entity plot has to always update, as does the category plot
#       - category plot might show same categories
#       - category plot might show different categories
