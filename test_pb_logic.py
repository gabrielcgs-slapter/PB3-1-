import pandas as pd
import pytest
from PB3 import _perform_data_comparison # Import the helper function

# Instructions for running tests:
# Ensure pytest is installed (pip install pytest).
# Run tests from the root directory of the project using the command: pytest

@pytest.fixture
def sample_caae_data():
    """Provides sample data for tests."""
    data = {
        'caae_1_no_change': {'caae': '1111.0001', 'email_html': '<p>CAAE 1 no change</p>'},
        'caae_2_content_changed_old': {'caae': '2222.0002', 'email_html': '<p>CAAE 2 old content</p>'},
        'caae_2_content_changed_new': {'caae': '2222.0002', 'email_html': '<p>CAAE 2 new content</p>'},
        'caae_3_removed': {'caae': '3333.0003', 'email_html': '<p>CAAE 3 will be removed</p>'},
        'caae_4_new': {'caae': '4444.0004', 'email_html': '<p>CAAE 4 is new</p>'},
        'caae_5_no_change_complex_html': {'caae': '5555.0005', 'email_html': '<div>Complex<br/>HTML structure</div><table><tr><td>Data</td></tr></table>'},
        'caae_6_content_changed_complex_old': {'caae': '6666.0006', 'email_html': '<div>Old Complex<br/>HTML</div>'},
        'caae_6_content_changed_complex_new': {'caae': '6666.0006', 'email_html': '<div>New Complex<br/>HTML different</div>'},
    }
    return data

def create_df(data_list):
    """Helper to create DataFrame from a list of dicts."""
    if not data_list:
        return pd.DataFrame(columns=['caae', 'email_html'])
    return pd.DataFrame(data_list)

def test_no_changes(sample_caae_data):
    """Test scenario where new_df and old_df are identical."""
    old_list = [sample_caae_data['caae_1_no_change'], sample_caae_data['caae_5_no_change_complex_html']]
    new_list = [sample_caae_data['caae_1_no_change'], sample_caae_data['caae_5_no_change_complex_html']]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 0
    assert len(updated_html_list) == 0

def test_content_changed(sample_caae_data):
    """Test scenario where content of existing CAAEs changes."""
    old_list = [
        sample_caae_data['caae_1_no_change'], 
        sample_caae_data['caae_2_content_changed_old'],
        sample_caae_data['caae_6_content_changed_complex_old']
    ]
    new_list = [
        sample_caae_data['caae_1_no_change'], 
        sample_caae_data['caae_2_content_changed_new'],
        sample_caae_data['caae_6_content_changed_complex_new']
    ]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 2
    assert len(updated_html_list) == 2
    assert sample_caae_data['caae_2_content_changed_new']['email_html'] in updated_html_list
    assert sample_caae_data['caae_6_content_changed_complex_new']['email_html'] in updated_html_list

def test_new_caae_added(sample_caae_data):
    """Test scenario where new CAAEs are added in new_df."""
    old_list = [sample_caae_data['caae_1_no_change']]
    new_list = [sample_caae_data['caae_1_no_change'], sample_caae_data['caae_4_new']]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 1
    assert len(updated_html_list) == 1
    assert sample_caae_data['caae_4_new']['email_html'] in updated_html_list

def test_caae_removed(sample_caae_data):
    """Test scenario where CAAEs are removed from new_df (present in old_df)."""
    old_list = [sample_caae_data['caae_1_no_change'], sample_caae_data['caae_3_removed']]
    new_list = [sample_caae_data['caae_1_no_change']]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    # Removed CAAEs should not be in the updated list as per current logic focus (new/changed content)
    assert num_updated == 0 
    assert len(updated_html_list) == 0

def test_mixed_changes_added_removed_content_changed(sample_caae_data):
    """Test a mix of additions, removals, and content changes."""
    old_list = [
        sample_caae_data['caae_1_no_change'],                  # No change
        sample_caae_data['caae_2_content_changed_old'],        # Content will change
        sample_caae_data['caae_3_removed']                     # Will be removed
    ]
    new_list = [
        sample_caae_data['caae_1_no_change'],                  # No change
        sample_caae_data['caae_2_content_changed_new'],        # Content changed
        sample_caae_data['caae_4_new']                         # New CAAE
    ]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 2 # caae_2 changed, caae_4 new
    assert len(updated_html_list) == 2
    assert sample_caae_data['caae_2_content_changed_new']['email_html'] in updated_html_list
    assert sample_caae_data['caae_4_new']['email_html'] in updated_html_list
    assert sample_caae_data['caae_3_removed']['email_html'] not in updated_html_list

def test_empty_new_df(sample_caae_data):
    """Test scenario where new_df is empty."""
    old_list = [sample_caae_data['caae_1_no_change']]
    new_list = []
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 0
    assert len(updated_html_list) == 0

def test_empty_old_df(sample_caae_data):
    """Test scenario where old_df is empty (simulates first run)."""
    old_list = []
    new_list = [sample_caae_data['caae_1_no_change'], sample_caae_data['caae_4_new']]
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    # All items in new_df are considered new
    assert num_updated == 2
    assert len(updated_html_list) == 2
    assert sample_caae_data['caae_1_no_change']['email_html'] in updated_html_list
    assert sample_caae_data['caae_4_new']['email_html'] in updated_html_list

def test_both_dfs_empty():
    """Test scenario where both new_df and old_df are empty."""
    old_list = []
    new_list = []
    old_df = create_df(old_list)
    new_df = create_df(new_list)

    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    assert num_updated == 0
    assert len(updated_html_list) == 0

def test_caae_column_missing():
    """Test behavior when 'caae' column is missing (should ideally handle gracefully or error)."""
    # The _perform_data_comparison function assumes 'caae' and 'email_html' columns.
    # Pandas merge will raise KeyError if 'on' column ('caae') is missing.
    # This test verifies that behavior or how it's handled if error handling was added to _perform_data_comparison.
    old_df = pd.DataFrame([{'some_other_col': 'data1', 'email_html': 'html1'}])
    new_df = pd.DataFrame([{'caae': '123', 'email_html': 'html_new'}])
    
    with pytest.raises(KeyError): # Expecting a KeyError due to missing 'caae' in old_df for merge
        _perform_data_comparison(new_df, old_df)

    new_df_missing_caae = pd.DataFrame([{'some_other_col': 'data2', 'email_html': 'html2'}])
    old_df_valid = pd.DataFrame([{'caae': '123', 'email_html': 'html_old'}])
    with pytest.raises(KeyError): # Expecting a KeyError due to missing 'caae' in new_df for merge
        _perform_data_comparison(new_df_missing_caae, old_df_valid)

def test_email_html_column_missing():
    """Test behavior when 'email_html' column is missing."""
    # The function relies on 'email_html_new' and 'email_html_old' after merge.
    # If these are missing, it might lead to KeyErrors or unexpected behavior.
    old_df = pd.DataFrame([{'caae': '123', 'other_html_col': 'html_old'}])
    new_df = pd.DataFrame([{'caae': '123', 'email_html': 'html_new'}])
    
    # This will result in 'email_html_old' being all NaN, and 'other_html_col_new'/'other_html_col_old'
    # The masks content_changed_mask and new_caae_mask will likely operate on mostly NaNs for _old side
    # and might not error out but produce logical errors in update detection depending on strictness.
    # Current logic should still run but might misinterpret 'updates'.
    # Specifically, new_caae_mask would be true for '123' because email_html_old would be NaN.
    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    assert num_updated == 1 # '123' will be seen as new because 'email_html_old' is NaN after merge
    assert new_df['email_html'].iloc[0] in updated_html_list

    old_df_valid = pd.DataFrame([{'caae': '123', 'email_html': 'html_old'}])
    new_df_missing_email = pd.DataFrame([{'caae': '123', 'other_html_col': 'html_new'}])
    # Here, 'email_html_new' will be NaN. content_changed_mask will be false. new_caae_mask will be false.
    updated_html_list, num_updated = _perform_data_comparison(new_df_missing_email, old_df_valid)
    assert num_updated == 0 # No 'email_html_new' to report
    assert len(updated_html_list) == 0

def test_data_types_consistency():
    """Test with consistent data types for 'caae'."""
    old_df = create_df([{'caae': 1111, 'email_html': 'html1'}]) # int CAAE
    new_df = create_df([{'caae': '1111', 'email_html': 'html1'}]) # string CAAE
    
    # Pandas merge might handle mixed types for 'on' column, but it's better to ensure consistency.
    # If types are different, they might not merge as expected, leading to all items in new_df seen as new.
    updated_html_list, num_updated = _perform_data_comparison(new_df, old_df)
    
    # If '1111' (int) and '1111' (str) are treated as different keys by merge:
    assert num_updated == 1 # new_df's '1111' will be considered new
    assert new_df['email_html'].iloc[0] in updated_html_list
    
    # For a true "no change" test with consistent types:
    old_df_str = create_df([{'caae': '7777', 'email_html': 'html_same'}])
    new_df_str = create_df([{'caae': '7777', 'email_html': 'html_same'}])
    updated_html_list_str, num_updated_str = _perform_data_comparison(new_df_str, old_df_str)
    assert num_updated_str == 0

    old_df_int = create_df([{'caae': 8888, 'email_html': 'html_same_int'}])
    new_df_int = create_df([{'caae': 8888, 'email_html': 'html_same_int'}])
    updated_html_list_int, num_updated_int = _perform_data_comparison(new_df_int, old_df_int)
    assert num_updated_int == 0
