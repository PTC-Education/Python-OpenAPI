# Python-OpenAPI
This repository stores the method to auto-generate all the REST API endpoints for Onshape (in Python). The official documentation of all API endpoints can be found [here](https://cad.onshape.com/glassworks/explorer/#/). 

To use the Python snippets in Jupyter notebooks, we recommend coding in Google Colab and follow the steps below to import the snippets to your own notebook: 

1. Download `API_Snippets.ipynb` from this repository. 
2. Upload `API_Snippets.ipynb` to your Google Drive with Google Colab available to your Google account. 
3. In your own project notebook (which you would like these API snippets imported into), go to "Tools" and select "Settings". Under "Site" on the left panel, you can copy and paste the URL of the uploaded `API_Snippets.ipynb` to the "Custome snippet notebook URL" textbox. 
4. Once you refresh the notebook, you should be able to see and import the code snippets under "Code Snippets" on the left panel of the webpage (the <> icon). 

Please note that you will need to first import and run section 0 from `API_Snippets.ipynb` for any project before other code snippets can function properly. 

For more information on obtaining your Onshape API keys, kindly follow the steps under section 2 of [this guide](https://github.com/PTC-Education/Onshape-Integration-Guides/blob/main/API_Intro.md#2-generating-your-onshape-api-keys). 

## Structure of this repository: 
- `API_Snippets.ipynb`: the main product of this repository with all Python-version API endpoints 
- `API_generator.py`: functions used to generate and format every API endpoint 
- `master_writer.py`: the main code used to generate the `API_Snippets.ipynb` 
