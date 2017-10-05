import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

class selectionTest(dml.Algorithm):
    contributor = 'bohorqux_rocksdan'
    reads = ['bohorqux_rocksdan.crimes', 'bohorqux_rocksdan.MBTA']
    writes = ['bohorqux_rocksdan.tuesday_crimes']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('bohorqux_rocksdan', 'bohorqux_rocksdan')

        crimes = repo['bohorqux_rocksdan.crimes']
        train_schedule = repo['bohorqux_rocksdan.MBTA']
        tuesday_reports = []
        train_reports = []
        union = []
        #SELECTION: Obtaining tuesday crime reports here
        for reports in crimes.find():
            if reports["DAY_OF_WEEK"] == 'Tuesday':
                tuesday_reports.append({"OFFENSE":reports["OFFENSE_CODE_GROUP"], "Desc":reports["OFFENSE_DESCRIPTION"], "SHOOTING":reports["SHOOTING"], "HOUR":reports["HOUR"], "STREET":reports["STREET"], "DAY":reports["DAY_OF_WEEK"]})
                
        #SELECTION: Obtaining tuesday train info
#        for trains in train_schedule.find():
#            if trains["weekday"] == "Tuesday":
#                train_reports.append(trains)

#        for i in range(len(tuesday_reports)):
#            union.append({tuesday_reports[i] + train_reports[i]})
        
        repo.dropCollection("tuesday_crimes")
        repo.createCollection("tuesday_crimes")

        repo['bohorqux_rocksdan.tuesday_crimes'].insert_many(tuesday_reports)
        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('bohorqux_rocksdan', 'bohorqux_rocksdan')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:bohorqux_rocksdan#selectionTest', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_crimes = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_crimes, this_script)
        doc.usage(get_crimes, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                   'ont:Query':'?OFFENSE_CODE_GROUP=Residential+Burglary&$select=OFFENSE_CODE_GROUP,Lat,Long,STREET'
                  }
                  )
        crimes = doc.entity('dat:bohorqux_rocksdan#tuesday_crimes', {prov.model.PROV_LABEL:'Tuesdays', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(crimes, this_script)
        doc.wasGeneratedBy(crimes, get_crimes, endTime)
        doc.wasDerivedFrom(crimes, resource, get_crimes, get_crimes, get_crimes)

        repo.logout()
                  
        return doc

selectionTest.execute()
doc = selectionTest.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof
