import os
import re
import psutil
import platform
import sqlite3 as sql
import pandas as pd
from pathlib import Path

"""
Tabelas:
    V - Machines
        ID:             Integer (Identifier Key)
        Name:           TEXT  (20)
        <Various hardware parameters such as OS, CPU cores, Accelerators, etc.>
    V - Programs:
        ID:             Integer (Identifier Key)
        Name:           TEXT  (20)

    V - Training_Datasets
        ID:             Integer (Identifier Key)
        Name:           TEXT  (20)
        Machine:        Integer (Foreign Key = Machines:ID)
        Program:        ID      (Foreign Key = Program:ID)
    
    V - Approximation_Techniques
        Name:           TEXT  (20)
        ID:             Integer (Identifier Key)
    
    V - Approximation_Metrics
        Program:        Integer (Foreign Key = Programs:ID)                     | Compound
        Dataset:        Integer (Foreign Key = Training_Datasets:ID)            | Identifier
        Technique:      Integer (Foreign Key = Approximation_Techniques:ID)     | Key
        <Various Precision Metrics as Float>
        <Execution historics such as energy spent, memory used, training time and estimation times>

    V - Autotuning_Techniques
        ID:             Integer (Identifier Key)
        Name:           TEXT  (20)

    V - Optimizations
        Program:        Integer (Foreign Key = Programs:ID)
        Autotuning:     Integer (Foreign Key = Autotuning_Techniques:ID)
        Machine:        Integer (Foreign Key = Machines:ID)
        Approximation:  Integer (Foreign Key = Approximation_Techniques:ID)
        Training_Data:  Integer (Foreign Key = Training_Datasets:ID)
        ID:             Integer (Unique value)                                  |Identifier key
"""

def CheckString(name, function):
    if not isinstance(name, str):
        raise Exception(f'{function} must be of type str, received {type(name)}')
    if len(name) > 32:
        raise Exception(f'maximum {function} length is 32 characters, received {len(name)}')
    if len(name) == 0:
        raise Exception(f'{function} must have at least one character, received empty string')
    if not name.isalnum():
        special_characters = set(re.findall(r"[^a-zA-Z0-9\s]", name))
        raise Exception(f'{function} must be an alphanumeric string, received string with {special_characters}')

def GetMachine(device_name):
        net_stats = psutil.net_if_stats()
        net_speeds = [net_stats[a].mtu for a in net_stats]
        while len(net_speeds) < 5:
            net_speeds.append(0)
        
        m = {
            'NAME':                     device_name,
            'OS':                       platform.system()[0:32],
            'RELEASE':                  platform.release()[0:32],
            'VERSION':                  platform.version()[0:32],
            'PROCESSOR_ARCHITECTURE1':  platform.architecture()[0][0:32],
            'PROCESSOR_ARCHITECTURE2':  platform.architecture()[1][0:32],
            'INSTRUCTION_SET':          platform.machine()[0:32],
            'CPU_CORES':                psutil.cpu_count(),
            'MEMORY':                   psutil.virtual_memory().total,
            'NIC0':                     net_speeds[0],
            'NIC1':                     net_speeds[1],
            'NIC2':                     net_speeds[2],
            'NIC3':                     net_speeds[3],
            'NIC4':                     net_speeds[4],
        }
        return m

class DatabaseManager:
    def __init__(self, database='default'):
        #Checar se banco de dados existe e o criar caso contrário
        #Conectar ao banco de dados e salvar conexão para uso futuro
        CheckString(database, 'database')
        self.database = 'database/' + database

        if not os.path.isfile(self.database+'db'):
            print(f'Creating database {self.database}')
            self._initialize_tables()
        else:
            print(f'Connecting to database {self.database}')
        self.db = sql.connect(self.database+'db')
        self.cursor = self.db.cursor()

    def _initialize_tables(self):
        db = sql.connect(self.database+'db')
        cursor = db.cursor()
        query = """
            CREATE TABLE MACHINES(
                ID                          INTEGER PRIMARY KEY,
                NAME                        TEXT(32),
                OS                          TEXT(32),
                RELEASE                     TEXT(32),
                VERSION                     TEXT(32),
                PROCESSOR_ARCHITECTURE1     TEXT(32),
                PROCESSOR_ARCHITECTURE2     TEXT(32),
                INSTRUCTION_SET             TEXT(32),
                CPU_CORES                   INTEGER,
                MEMORY                      BIGINT,
                NIC0                        INTEGER,
                NIC1                        INTEGER,
                NIC2                        INTEGER,
                NIC3                        INTEGER,
                NIC4                        INTEGER
            );
        """
        cursor.execute(query)
        query = """
            CREATE TABLE PROGRAMS(
                ID      INTEGER PRIMARY KEY,
                NAME    TEXT(32)
            );
        """
        cursor.execute(query)
        query = f"""
            CREATE TABLE DATASETS(
                ID          INTEGER PRIMARY KEY,
                NAME        TEXT(32),
                MACHINE     INTEGER,
                PROGRAM     INTEGER,
                FOREIGN KEY (MACHINE) REFERENCES MACHINES(ID),
                FOREIGN KEY (PROGRAM) REFERENCES PROGRAMS(ID)
            );
        """
        cursor.execute(query)
        query = f"""
            CREATE TABLE APPROXIMATION_TECHNIQUES(
                ID      INTEGER PRIMARY KEY,
                NAME    TEXT(32)
            );
        """
        cursor.execute(query)

        query = f"""
            CREATE TABLE APPROXIMATIONS(
                ID          INTEGER PRIMARY KEY,
                PROGRAM                 INTEGER,
                TRAINING_DATASET        INTEGER,
                TESTING_DATASET         INTEGER,
                TECHNIQUE               INTEGER,
                TRAINING_TIME           INTEGER,
                TRAINING_ENERGY         INTEGER,
                TRAINING_TEMPERATURE    INTEGER,
                TRAINING_MEMORY         INTEGER,
                FOREIGN KEY (PROGRAM) REFERENCES PROGRAMS(ID),
                FOREIGN KEY (TRAINING_DATASET) REFERENCES DATASETS(ID),
                FOREIGN KEY (TESTING_DATASET) REFERENCES DATASETS(ID),
                FOREIGN KEY (TECHNIQUE) REFERENCES APPROXIMATION_TECHNIQUES(ID)
            );
        """
        cursor.execute(query)

        query = f"""
            CREATE TABLE APPROXIMATION_METRICS(
                APPROXIMATION           INTEGER PRIMARY KEY,
                --MISCELANEOUS METRICS
                FOREIGN KEY (APPROXIMATION) REFERENCES APPROXIMATIONS(ID)
            );
        """
        cursor.execute(query)
        query = f"""
            CREATE TABLE AUTOTUNING_TECHNIQUES(
                ID      INTEGER PRIMARY KEY,
                NAME    TEXT(32)
            );
        """
        cursor.execute(query)
        query = f"""
            CREATE TABLE OPTIMIZATIONS(
                ID              INTEGER PRIMARY KEY,
                PROGRAM         INTEGER,
                AUTOTUNING      INTEGER,
                MACHINE         INTEGER,
                APPROXIMATION   INTEGER,
                DATASET         INTEGER,
                FOREIGN KEY (PROGRAM) REFERENCES PROGRAMS(ID),
                FOREIGN KEY (AUTOTUNING) REFERENCES AUTOTUNING_TECHNIQUES(ID),
                FOREIGN KEY (MACHINE) REFERENCES MACHINES(ID),
                FOREIGN KEY (APPROXIMATION) REFERENCES APPROXIMATION_TECHNIQUES(ID),
                FOREIGN KEY (DATASET) REFERENCES DATASETS(ID)
            );
        """
        cursor.execute(query)
        query = f"""
            CREATE TABLE OPTIMIZATION_PERFORMANCE(
                OPTIMIZATION    INTEGER PRIMARY KEY,
                TEMPORARY       INTEGER,
                --ADD METRICS LATER
                FOREIGN KEY (OPTIMIZATION) REFERENCES OPTIMIZATIONS(ID)
            );
        """
        cursor.execute(query)

        db.commit()

    def InsertMachine(self, machine):
        CheckString(machine['NAME'], 'machine')
        if not isinstance(machine['OS'], str):
            raise Exception(f'OS parameter must be str, received {type(machine['OS'])}')
        if not isinstance(machine['RELEASE'], str):
            raise Exception(f'RELEASE parameter must be str, received {type(machine['RELEASE'])}')        
        if not isinstance(machine['VERSION'], str):
            raise Exception(f'VERSION parameter must be str, received {type(machine['VERSION'])}')
        if not isinstance(machine['PROCESSOR_ARCHITECTURE1'], str):
            raise Exception(f'PROCESSOR_ARCHITECTURE1 parameter must be str, received {type(machine['PROCESSOR_ARCHITECTURE1'])}')
        if not isinstance(machine['PROCESSOR_ARCHITECTURE2'], str):
            raise Exception(f'PROCESSOR_ARCHITECTURE2 parameter must be str, received {type(machine['PROCESSOR_ARCHITECTURE2'])}')
        if not isinstance(machine['INSTRUCTION_SET'], str):
            raise Exception(f'INSTRUCTION_SET parameter must be str, received {type(machine['INSTRUCTION_SET'])}')
        if not isinstance(machine['CPU_CORES'], int):
            raise Exception(f'CPU_CORES parameter must be int, received {type(machine['CPU_CORES'])}')
        if not isinstance(machine['MEMORY'], int):
            raise Exception(f'MEMORY parameter must be int, received {type(machine['MEMORY'])}')
        if not isinstance(machine['NIC0'], int):
            raise Exception(f'NIC0 parameter must be int, received {type(machine['NIC0'])}')
        if not isinstance(machine['NIC1'], int):
            raise Exception(f'NIC1 parameter must be int, received {type(machine['NIC1'])}')
        if not isinstance(machine['NIC2'], int):
            raise Exception(f'NIC2 parameter must be int, received {type(machine['NIC2'])}')
        if not isinstance(machine['NIC3'], int):
            raise Exception(f'NIC3 parameter must be int, received {type(machine['NIC3'])}')
        if not isinstance(machine['NIC4'], int):
            raise Exception(f'NIC4 parameter must be int, received {type(machine['NIC4'])}')

        query = f"""SELECT * FROM MACHINES WHERE NAME = '{machine['NAME']}';"""
        ans = self.cursor.execute(query).fetchone()
        if ans != None:
            return ans[0]

        query = f"""
            INSERT INTO MACHINES (
                NAME,
                OS,
                RELEASE,
                VERSION,
                PROCESSOR_ARCHITECTURE1,
                PROCESSOR_ARCHITECTURE2,
                INSTRUCTION_SET,
                CPU_CORES,
                MEMORY,
                NIC0,
                NIC1,
                NIC2,
                NIC3,
                NIC4
            ) VALUES (
                '{machine['NAME']}',
                '{machine['OS']}',
                '{machine['RELEASE']}',
                '{machine['VERSION']}',
                '{machine['PROCESSOR_ARCHITECTURE1']}',
                '{machine['PROCESSOR_ARCHITECTURE2']}',
                '{machine['INSTRUCTION_SET']}',
                {machine['CPU_CORES']},
                {machine['MEMORY']},
                {machine['NIC0']},
                {machine['NIC1']},
                {machine['NIC2']},
                {machine['NIC3']},
                {machine['NIC4']});"""
        self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveMachineID(self, NAME):
        NAME = NAME[0:32]
        query = f"""SELECT ID FROM MACHINES WHERE NAME = '{NAME}';"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RetrieveMachineData(self, ID):
        if not isinstance(ID, int):
            raise Exception(f'ID must be int, received {type(ID)}')
        query = f"""SELECT NAME, OS, RELEASE, VERSION, PROCESSOR_ARCHITECTURE1, PROCESSOR_ARCHITECTURE2, INSTRUCTION_SET, CPU_CORES, MEMORY, NIC0, NIC1, NIC2, NIC3, NIC4 FROM MACHINES WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        if ans == None:
            return None
        ans = {
            'NAME': ans[0],
            'OS': ans[1],
            'RELEASE': ans[2],
            'VERSION': ans[3],
            'PROCESSOR_ARCHITECTURE1': ans[4],
            'PROCESSOR_ARCHITECTURE2': ans[5],
            'INSTRUCTION_SET': ans[5],
            'CPU_CORES': ans[6],
            'MEMORY': ans[7],
            'NIC0': ans[8],
            'NIC1': ans[9],
            'NIC2': ans[10],
            'NIC3': ans[11],
            'NIC4': ans[12],
        }
        return ans
    def RemoveMachine(self, ID):
        query = f"""SELECT (ID) FROM DATASETS WHERE PROGRAM={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveDataset(child)
        query = f"""SELECT (ID) FROM OPTIMIZATIONS WHERE PROGRAM={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveAutotuningHist(child)

        query = f"""DELETE FROM MACHINES WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()

    def InsertProgram(self, PROGRAM):
        CheckString(PROGRAM, 'PROGRAM')
        query = f"""SELECT * FROM PROGRAMS WHERE NAME = '{PROGRAM}';"""
        ans = self.cursor.execute(query).fetchone()
        if ans != None:
            return ans[0]
        
        query = f"""INSERT INTO PROGRAMS (NAME) VALUES ('{PROGRAM}');"""
        self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveProgramID(self, NAME):
        NAME = NAME[0:32]
        query = f"""SELECT ID FROM PROGRAMS WHERE NAME = '{NAME}';"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RetrieveProgram(self, ID):
        query = f"""SELECT NAME FROM PROGRAMS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RemoveProgram(self, ID):
        query = f"""SELECT (ID) FROM DATASETS WHERE PROGRAM={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveDataset(child)
        query = f"""SELECT (ID) FROM APPROXIMATIONS WHERE PROGRAM={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveApproxHist(child)
        query = f"""SELECT (ID) FROM OPTIMIZATIONS WHERE PROGRAM={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveAutotuningHist(child)

        query = f"""DELETE FROM PROGRAMS WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()

    def InsertAutotuningTech(self, TECHNIQUE):
        CheckString(TECHNIQUE, 'TECHNIQUE')
        query = f"""SELECT * FROM AUTOTUNING_TECHNIQUES WHERE NAME = '{TECHNIQUE}';"""
        ans = self.cursor.execute(query).fetchone()
        if ans != None:            
            return ans[0]
                
        query = f"""INSERT INTO AUTOTUNING_TECHNIQUES (NAME) VALUES ('{TECHNIQUE}');"""
        self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveAutotuningTechID(self, NAME):
        NAME = NAME[0:32]
        query = f"""SELECT ID FROM AUTOTUNING_TECHNIQUES WHERE NAME = '{NAME}';"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RetrieveAutotuningTech(self, ID):
        query = f"""SELECT NAME FROM AUTOTUNING_TECHNIQUES WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RemoveAutotuningTech(self, ID):
        query = f"""SELECT (ID) FROM OPTIMIZATIONS WHERE AUTOTUNING={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveAutotuningHist(child)

        query = f"""DELETE FROM AUTOTUNING_TECHNIQUES WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()

    def InsertApproxTech(self, TECHNIQUE):
        query = f"""SELECT * FROM APPROXIMATION_TECHNIQUES WHERE NAME = '{TECHNIQUE}';"""
        ans = self.cursor.execute(query).fetchone()
        if ans != None:
            return ans[0]
                        
        query = f"""INSERT INTO APPROXIMATION_TECHNIQUES (NAME) VALUES ('{TECHNIQUE}');"""
        self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveApproxTechID(self, NAME):
        NAME = NAME[0:32]
        query = f"""SELECT ID FROM APPROXIMATION_TECHNIQUES WHERE NAME = '{NAME}';"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RetrieveApproxTech(self, ID):
        query = f"""SELECT NAME FROM APPROXIMATION_TECHNIQUES WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[0] if ans != None else None
    def RemoveApproxTech(self, ID):
        query = f"""SELECT (ID) FROM OPTIMIZATIONS WHERE APPROXIMATION={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveAutotuningHist(child)

        query = f"""SELECT (ID) FROM APPROXIMATIONS WHERE TECHNIQUE={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveApproxHist(child)

        query = f"""SELECT (ID) FROM DATASETS WHERE ID={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveDataset(child)

        query = f"""DELETE FROM APPROXIMATION_TECHNIQUES WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()

    def InsertAutotuningHist(self, PROGRAM, AUTOTUNING_TECHNIQUE, MACHINE, APPROXIMATION_TECHNIQUE, DATASET, historic):
        if APPROXIMATION_TECHNIQUE == None:
            APPROXIMATION_TECHNIQUE = 0
        if DATASET == None:
            DATASET = 0
        query = f"""INSERT INTO OPTIMIZATIONS (PROGRAM, AUTOTUNING, MACHINE, APPROXIMATION, DATASET) VALUES ({PROGRAM}, {AUTOTUNING_TECHNIQUE}, {MACHINE}, {APPROXIMATION_TECHNIQUE}, {DATASET});"""
        self.cursor.execute(query)
        self.db.commit()
        id = self.cursor.lastrowid

        path = f"""{self.database}/optimizations/{self.RetrieveProgram(PROGRAM)}/{self.RetrieveMachineData(MACHINE)['NAME']}/{self.RetrieveAutotuningTech(AUTOTUNING_TECHNIQUE)}/"""
        if APPROXIMATION_TECHNIQUE != 0:
            path = path + f"""{self.RetrieveApproxTech(APPROXIMATION_TECHNIQUE)}/{self.RetrieveDatasetData(DATASET)}/"""
        else:
            path = path + f"""NO_APPROXIMATION/"""
        Path(path).mkdir(parents=True, exist_ok=True)

        historic = pd.DataFrame(historic)

        historic.to_parquet(path+str(id)+'.parquet')
        return id
    def RetrieveAutotuningHist(self, ID):
        query = f"""SELECT * FROM OPTIMIZATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        path = f"""{self.database}/optimizations/{self.RetrieveProgram(ans[1])}/{self.RetrieveMachineData(ans[3])['NAME']}/{self.RetrieveAutotuningTech(ans[2])}/"""
        if ans[4] != 0:
            path = path + f"""{self.RetrieveApproxTech(ans[4])}/{self.RetrieveDatasetData(ans[5])}/"""
        else:
            path = path + f"""NO_APPROXIMATION/"""
        path = path + str(ID)
        data = {
            'ID':               ans[0],
            'program':          self.RetrieveProgram(ans[1]),
            'machine':          self.RetrieveMachineData(ans[3])['NAME'],
            'autotuning':       self.RetrieveAutotuningTech(ans[2]),
            'approximation':    self.RetrieveApproxTech(ans[4]) if ans[4] != 0 else 0,
            'dataset':          self.RetrieveDatasetData(ans[5]) if ans[4] != 0 else 0,
            'data':             pd.read_parquet(path+'.parquet')
        }
        return data
    def RetrieveAutotuningHistData(self, ID):
        query = f"""SELECT * FROM OPTIMIZATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        path = f"""{self.database}/optimizations/{self.RetrieveProgram(ans[1])}/{self.RetrieveMachineData(ans[3])['NAME']}/{self.RetrieveAutotuningTech(ans[2])}/"""
        if ans[4] != 0:
            path = path + f"""{self.RetrieveApproxTech(ans[4])}/{self.RetrieveDatasetData(ans[5])}/"""
        else:
            path = path + f"""NO_APPROXIMATION/"""
        path = path + str(ID)
        return {
            'ID':               ans[0],
            'program':          self.RetrieveProgram(ans[1]),
            'machine':          self.RetrieveMachineData(ans[3])['NAME'],
            'autotuning':       self.RetrieveAutotuningTech(ans[2]),
            'approximation':    self.RetrieveApproxTech(ans[4]) if ans[4] != 0 else 0,
            'dataset':          self.RetrieveDatasetData(ans[5]) if ans[4] != 0 else 0,
            'data':             path+'.parquet'
            }
    def RetrieveProgramAutotuning(self, PROGRAM):
        query = f"""
            SELECT * FROM OPTIMIZATIONS WHERE (PROGRAM={PROGRAM});
        """
        ans = self.cursor.execute(query).fetchall()
        return ans
    def RemoveAutotuningHist(self, ID):
        self.RemoveAutotuningPerf(ID)

        query = f"""SELECT * FROM OPTIMIZATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        
        query = f"""DELETE FROM OPTIMIZATIONS WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()
        
        path = []
        path.append(f'{self.database}/optimizations/')
        path.append(f"""{self.RetrieveProgram(ans[1])}/""")
        path.append(f"""{self.RetrieveMachineData(ans[2])['NAME']}/""")
        path.append(f"""{self.RetrieveAutotuningTech(ans[3])}/""")
        if ans[5] != 0:
            path.append(f"""{self.RetrieveApproxTech(ans[4])}/""")
            path.append(f"""{self.RetrieveDatasetData(ans[5])}/""")
        else:
            path.append(f"""NO_APPROXIMATION/""")
        path.append(str(ans[0])+'.parquet')
        os.remove(''.join(path))
        path.pop()
        while len(path) > 0:
            if len(os.listdir(''.join(path))) > 0:
                break
            else:
                os.rmdir(''.join(path))
            path.pop()

    def InsertDataset(self, NAME, PROGRAM, MACHINE, data):
        query = f"""INSERT INTO DATASETS (NAME, PROGRAM, MACHINE) VALUES ('{NAME}', '{PROGRAM}', '{MACHINE}');"""
        self.cursor.execute(query)
        self.db.commit()
        id = self.cursor.lastrowid
        path = f"""{self.database}/datasets/{self.RetrieveProgram(PROGRAM)}/{self.RetrieveMachineData(MACHINE)['NAME']}/{NAME}/"""
        Path(path).mkdir(parents=True, exist_ok=True)

        dataset = pd.DataFrame(data)
        dataset.to_parquet(path+f'{id}'+'.parquet')
        return id
    def RetrieveDataset(self, ID):
        query = f"""SELECT * FROM DATASETS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        path = f"""{self.database}/datasets/{self.RetrieveProgram(ans[3])}/{self.RetrieveMachineData(ans[2])['NAME']}/{ans[1]}/"""
        dataframe = pd.read_parquet(path+f'{ans[0]}' + '.parquet')
        return dataframe
    def RetrieveDatasetData(self, ID):
        query = f"""SELECT * FROM DATASETS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[1]
    def RemoveDataset(self, ID):
        query = f"""SELECT (ID) FROM APPROXIMATIONS WHERE DATASET={ID};"""
        self.cursor.execute(query)
        children = self.cursor.fetchall()
        children = [child[0] for child in children]
        for child in children:
            self.RemoveApproxHist(child)


        query = f"""SELECT * FROM DATASETS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
                        
        query = f"""DELETE FROM DATASETS WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()
        path = []
        path.append(f'{self.database}/datasets/')
        path.append(f"""{self.RetrieveProgram(ans[2])}/""")
        path.append(f"""{self.RetrieveMachineData(ans[3])['NAME']}/""")
        path.append(f"""{ans[1]}/""")
        path.append(f"""{ans[0]}.parquet""")
        os.remove(''.join(path))
        path.pop()
        while len(path) > 0:
            if len(os.listdir(''.join(path))) > 0:
                break
            else:
                os.rmdir(''.join(path))
            path.pop()

    def InsertApproxHist(self, PROGRAM, TRAINING_DATASET, TESTING_DATASET, APPROXIMATION_TECHNIQUE, training_values, testing_history):
        print(f'program {PROGRAM}') 
        print(f'training {TRAINING_DATASET}')
        print(f'testing {TESTING_DATASET}')
        print(f'approximator {APPROXIMATION_TECHNIQUE}')
        print(f'TRAINING_TIME, TRAINING_ENERGY, TRAINING_TEMPERATURE, TRAINING_MEMORY {training_values}')
        print(f'estimates {testing_history}')
        query = f"""INSERT INTO APPROXIMATIONS (PROGRAM, TRAINING_DATASET, TESTING_DATASET, TECHNIQUE, TRAINING_TIME, TRAINING_ENERGY, TRAINING_TEMPERATURE, TRAINING_MEMORY) VALUES ({PROGRAM}, {TRAINING_DATASET}, {TESTING_DATASET}, {APPROXIMATION_TECHNIQUE}, {training_values[0]}, {training_values[1]}, {training_values[2]}, {training_values[3]});"""
        self.cursor.execute(query)
        self.db.commit()
        id = self.cursor.lastrowid

        path = f"""{self.database}/approximations/{self.RetrieveProgram(PROGRAM)}/{self.RetrieveDatasetData(TRAINING_DATASET)}/{self.RetrieveDatasetData(TESTING_DATASET)}/{self.RetrieveApproxTech(APPROXIMATION_TECHNIQUE)}/"""
        Path(path).mkdir(parents=True, exist_ok=True)
        histories= pd.DataFrame(testing_history)        
        histories.to_parquet(path+str(id)+'.parquet')
        return id
    def RetrieveApproxHist(self, ID):
        query = f"""SELECT * FROM APPROXIMATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        path = f"""{self.database}/approximations/{self.RetrieveProgram(ans[1])}/{self.RetrieveDatasetData(ans[2])}/{self.RetrieveDatasetData(ans[3])}/{self.RetrieveApproxTech(ans[4])}/{ans[0]}"""
        dataframe = pd.read_parquet(path+'.parquet')
        return dataframe
    def RetrieveApproxHistData(self, ID):
        query = f"""SELECT * FROM APPROXIMATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans
    def RetrieveProgramApproxHist(self, PROGRAM):
        query = f"""SELECT * FROM APPROXIMATIONS WHERE (PROGRAM={PROGRAM});"""
        ans = self.cursor.execute(query).fetchall()
        return ans
    def RemoveApproxHist(self, ID):
        self.RemoveApproxPrec(ID)
        
        query = f"""SELECT * FROM APPROXIMATIONS WHERE ID = {ID};"""
        ans = self.cursor.execute(query).fetchone()
                
        query = f"""DELETE FROM APPROXIMATIONS WHERE ID={ID};"""
        self.cursor.execute(query)
        self.db.commit()

        path = []
        path.append(f'{self.database}/approximations/')
        path.append(f"""{self.RetrieveProgram(ans[1])}/""")
        path.append(f"""{self.RetrieveDatasetData(ans[2])}/""")
        path.append(f"""{self.RetrieveApproxTech(ans[3])}/""")
        path.append(f"""{ans[0]}.parquet""")
        os.remove(''.join(path))
        path.pop()
        while len(path) > 0:
            if len(os.listdir(''.join(path))) > 0:
                break
            else:
                os.rmdir(''.join(path))
            path.pop()

    def InsertApproxPrec(self, APPROXIMATION_HISTORY, data):
        query = f"""SELECT * FROM APPROXIMATION_METRICS WHERE APPROXIMATION={APPROXIMATION_HISTORY};"""
        ans = self.cursor.execute(query).fetchone()
        if ans != None:
            query = f"""UPDATE APPROXIMATION_METRICS SET TEMPORARY={data} WHERE APPROXIMATION={APPROXIMATION_HISTORY};"""
            self.cursor.execute(query)
        else:
            query = f"""INSERT INTO APPROXIMATION_METRICS (APPROXIMATION, TEMPORARY) VALUES ({APPROXIMATION_HISTORY}, {data});"""
            self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveApproxPrec(self, ID):
        query = f"""SELECT * FROM APPROXIMATION_METRICS WHERE APPROXIMATION = {ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[1]
    def RemoveApproxPrec(self, ID):
        query = f"""DELETE FROM APPROXIMATION_METRICS WHERE APPROXIMATION={ID};"""
        self.cursor.execute(query)
        self.db.commit()

    def InsertAutotuningPerf(self, AUTOTUNINGHISTORY, data):
        query = f"""SELECT * FROM OPTIMIZATION_PERFORMANCE WHERE OPTIMIZATION={AUTOTUNINGHISTORY};"""
        ans = self.cursor.execute(query).fetchone()        
        if ans != None:
            query = f"""UPDATE OPTIMIZATION_PERFORMANCE SET TEMPORARY={data} WHERE OPTIMIZATION={AUTOTUNINGHISTORY};"""
            self.cursor.execute(query)
        else:
            query = f"""INSERT INTO OPTIMIZATION_PERFORMANCE (OPTIMIZATION, TEMPORARY) VALUES ({AUTOTUNINGHISTORY}, {data});"""
            self.cursor.execute(query)
        self.db.commit()
        return self.cursor.lastrowid
    def RetrieveAutotuningPerf(self, ID):       #Retrieve Performance with specified ID
        query = f"""SELECT * FROM OPTIMIZATION_PERFORMANCE WHERE OPTIMIZATION={ID};"""
        ans = self.cursor.execute(query).fetchone()
        return ans[1]
    def RemoveAutotuningPerf(self, ID):
        query = f"""DELETE FROM OPTIMIZATION_PERFORMANCE WHERE OPTIMIZATION={ID};"""
        self.cursor.execute(query)
        self.db.commit()
