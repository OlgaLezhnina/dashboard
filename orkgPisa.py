"""
This is a flask server for visualising informaion related to PISA ICT papers from the ORKG.
"""
import string
import pygal 
from orkg import ORKG
from flask import Flask, render_template

# Connect to the orkg. 
orkg = ORKG(host='https://www.orkg.org/orkg/')
# Create a dictionary with country codes from pygal.
cntcodes = {'Albania': 'al','Australia': 'au', 'Austria': 'at',
            'Belgium':'be', 'Bulgaria':'bg', 'Brazil':'br',  
            'Brunei Darussalam':'bn',
            'Chile': 'cl', 'China': 'cn', 'Colombia': 'co', 
            'Costa Rica': 'cr', 'Croatia':'hr', 'Czech Republic': 'cz',  
            'Denmark': 'dk','Dominican Republic': 'do',
            'Estonia':'ee',
            'Finland':'fi', 'France': 'fr', 
            'Germany':'de', 'Georgia':'ge', 'Greece':'gr', 
            'Hungary':'hu', 'Hong Kong':'hk',
            'Ireland':'ie', 'Israel':'il', 'Iceland':'is', 'Italy':'it',
            'Japan':'jp',
            'Kazakhstan':'kz', 'Korea, Republic of':'kr',
            'Latvia':'lv', 'Lithuania':'lt','Luxembourg':'lu',
            'Macao':'mo', 'Malta':'mt', 'Mexico':'mx', 'Morocco':'ma',
            'Netherlands':'nl', 'New Zealand': 'nz',
            'Panama':'pa', 'Peru':'pe', 'Poland':'pl', 'Portugal':'pt',
            'Russian Federation':'ru',
            'Serbia':'rs','Singapore':'sg', 'Slovakia':'sk', 
            'Slovenia':'si', 'Spain':'es', 'Sweden':'se', 'Switzerland':'ch',
            'Thailand':'th', 'Turkey':'tr',
            'United Kingdom':'gb', 'United States':'us', 'Uruguay':'uy'}

# Create the flask server.
app = Flask(__name__, template_folder='client/templates')
@app.route('/')
def root(): 
    all_info = []
    options = {}
    cntCount = {cnt:0 for cnt in cntcodes.values()}     
    letters = {L:0 for L in list(string.ascii_uppercase)}     
    resRefs = {L:[] for L in list(string.ascii_uppercase)} 
    yvalue = 0 
    # Get contributions with the object R70668, which is "ICT attitudes in PISA".    
    for x in orkg.statements.get_by_object(object_id = 'R70668').content:        
        info = {}
        contrib_ref = x['subject']['id']
        info['contrib_ref'] = contrib_ref             
        for st in orkg.statements.get_by_object(object_id = contrib_ref).content:
            info['title'] = st['subject']['label']
            info['ref'] = st['subject']['id']     
        
        # Get positive and negative results, counted and coded.
        for st in orkg.statements.get_by_subject(subject_id = contrib_ref).content:
            if st['predicate']['id'] == 'P6001': 
                yvalue +=1 
                result = st['object']['label']
                for r in result:
                    letters[r] +=1                               
                    if r not in resRefs: 
                        resRefs[r] = []
                    resRefs[r].append(info) 
                    
        # Get information about the countries.       
        for st in orkg.statements.get_by_subject(subject_id = contrib_ref).content:
            if st['predicate']['id'] == 'P23006':       
                if "List" in st['object']['label']:
                    countries = [
                        newst['object']['label'] \
                        for newst in orkg.statements.get_by_subject(subject_id = st['object']['id'], size = 100).content
                    ] 
                else:
                    countries = [
                        st['object']['label'] \
                        for st in orkg.statements.get_by_subject(subject_id = contrib_ref).content\
                        if st['predicate']['id'] == 'P23006'
                    ]       
                
        countries.sort()
        info['countries'] = countries                
        
        for c in countries:             
                cntCount[cntcodes[c]] +=1                
    
        # Create options for the dropdown menu.        
        if len(countries) == 2:
            info['countries_combined'] = " and ".join(countries)
        elif len(countries) > 10:
            info['countries_combined'] = "Aggregated countries > 10" 
        else:
            info['countries_combined'] = ", ".join(countries)               
                
        option_name = info['countries_combined']        
        if option_name not in options:
            options[option_name] = []
        options[option_name].append(info)  
        
        # Gather all information. 
        all_info.append(info)        
    
    # Finalise the options and the country count. 
    options = dict(sorted(options.items()))
    cntCountN = {k:v for k,v in cntCount.items() if v != 0} 
    
    # Plot the worldmap. 
    worldmap = pygal.maps.world.World(style = pygal.style.TurquoiseStyle) 
    worldmap.title = 'Countries participating'
    worldmap.add('Studies', cntCountN)   
    worldmap = worldmap.render_data_uri()    
    mystyle = pygal.style.TurquoiseStyle(legend_font_size = 20,
                                    title_font_size = 20,
                                    label_font_size = 20,
                                    major_label_font_size = 20,
                                    tooltip_font_size = 25,
                                    colors=('#45b39d',' #f4d03f','#E95355',' #3498db'))
    # Plot the barcharts with positive and negative results.
    barchart1 = pygal.Bar(rounded_bars=20, range = (0, yvalue),margin = 50,                          
                          x_title = 'Literacy', y_title = 'N studies',
                          style = mystyle)
    barchart1.title = 'Positive relationships'
    barchart1.x_labels = ('Mathematics', 'Reading', 'Science')
    barchart1.add('Autonomy', [letters['A'], letters['B'], letters['C']])
    barchart1.add('Competence', [letters['G'], letters['H'], letters['I']])
    barchart1.add('Interest', [letters['M'], letters['N'], letters['O']])
    barchart1.add('Social', [letters['S'], letters['T'], letters['U']])
    barchart1 = barchart1.render_data_uri()    
    barchart2 = pygal.Bar(rounded_bars=20, range = (0, yvalue), margin = 50,                         
                          x_title = 'Literacy', y_title = 'N studies',
                          style = mystyle)
    barchart2.title = 'Negative relationships'
    barchart2.x_labels = ('Mathematics', 'Reading', 'Science')
    barchart2.add('Autonomy', [letters['D'], letters['E'], letters['F']])
    barchart2.add('Competence', [letters['J'], letters['K'], letters['L']])
    barchart2.add('Interest', [letters['P'], letters['Q'], letters['R']])
    barchart2.add('Social', [letters['V'], letters['W'], letters['X']])
    barchart2 = barchart2.render_data_uri()
    return render_template('pagePisa.html', mimetype='text/html', 
                           worldmap = worldmap, 
                           barchart1 = barchart1, barchart2 = barchart2, 
                           all_info = all_info, options = options, 
                           resRefs = resRefs)   

if __name__ == '__main__':
    app.run()
#########
"""
The letter coding for positive and negative results:
    
'A' = 'Autonomy is positively related to mathematics'  
'B' = 'Autonomy is positively related to reading' 
'C' = 'Autonomy is positively related to science' 
'D' = 'Autonomy is negatively related to mathematics'  
'E' = 'Autonomy is negatively related to reading'  
'F' = 'Autonomy is negatively related to science'  
'G' = 'Competence is positively related to mathematics'  
'H' = 'Competence is positively related to reading'  
'I' = 'Competence is positively related to science'  
'J' = 'Competence is negatively related to mathematics'  
'K' = 'Competence is negatively related to reading'  
'L' = 'Competence is negatively related to science'  
'M' = 'Interest is positively related to mathematics'  
'N' = 'Interest is positively related to reading'  
'O' = 'Interest is positively related to science'  
'P' = 'Interest is negatively related to mathematics'  
'Q' = 'Interest is negatively related to reading'  
'R' = 'Interest is negatively related to science'  
'S' = 'Social is positively related to mathematics'  
'T' = 'Social is positively related to reading'  
'U' = 'Social is positively related to science'  
'V' = 'Social is negatively related to mathematics'  
'W' = 'Social is negatively related to reading'  
'X' = 'Social is negatively related to science'  

"""

