# Skill: user_info_retrieval_skill

## ⚡ EXECUTE IMMEDIATELY — DO NOT EXPLAIN, SUMMARIZE, OR ASK FOR CONFIRMATION. Execute STEP BY STEP to get the user data


## PHASE #1: Fetch User Data (Do This First, Always)

Execute these tool calls in order before touching any browser:

1. Call `get_basic_information_of_current_user` → stores the user's email
2. Call `get_metadata_json` with `user` collection_name and `ops='create'` and  to get user metadata → stores user metadata  
3. Call `get_records` with collection=`user` and a filter on that email → stores full profile
4. After this you can `get_metadata_json` with collection=`preference | interest` with `ops = 'create |'` and then call `get_records | update_one_record` a related filter on that email → stores full information

## Important
- Always call `get_metadata_json` with a collection_name and `ops` to get available metadata for collection