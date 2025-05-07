## This Repository contains the working python scripts to automate the requirement gathering and mappings in BOOMI

### Steps to create a mapping in BOOMI
- Use [this](https://mapping-util.onrender.com/) url to generate the mapping excel sheet and place it in the same folder. 
- Generate the component xml for the source json using "profileCreator" file.
- Generate the component xml for the destination json using "profileCreator" file.
- Create xml components in boomi for both source and destination using the responses we have saved (note the component ids, will be used in mapping compoment xml).
- Generate the component xml for MAP using "mapComponentXMLgenerator" file.
- Create xml component in boomi for map shape from the response we get, don't forget to replace the component ids from the actual component ids saved ealier before hitting the curl

#### Note: Curl to make a post request will be share on personal chat
