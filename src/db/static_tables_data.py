vehicle_statuses = ["Maintenance", "Inactive", "Idle", "Running", "Breakdown" , "Under Maintenance"]



task_statuses = ['Pending' , 'Ongoing' , 'Completed' , 'Delay' , 'Cancelled' , 'Schedule_changed']




driver_roles = ['Primary' , 'Secondary' , 'Tertiary1' , 'Tertiary2' , 'Supervisor']


fuel_types = ['PETROL', 'DIESEL', 'CNG', 'LPG', 'LNG', 'ELECTRIC(BEV)', 'ELECTRIC(BOV)', 'HYBRID(HEV)', 'HYBRID(PHEV)', 'FCEV']



attendance_states = ['Present' , 'Absent', 'No action' ,  'Expired']


driver_vehicle_connected_time_states = ['No action' , 'Early' , 'On time' ,  'Late' ]

unlock_states = ['Success' , 'Failure' , 'Unauthorized' , 'Time_out' , 'Vehicle_bluetooth_inactive']


model_types = ['Exclusive_schedule_single' , 'Exclusive_schedule_multiple' , 'Hybrid' , 'Onspot']

sub_model_types = ['Porter' , 'Avaronn_task']



request_status = ['Pending' , 'Viewed' , 'Approved' , 'Rejected']

leave_types = ["Sick" , "Personal" , "Unpaid"]

task_types = {"Attendance": 10.0 ,
              "Trip start" :20.0, 
              "Trip off":20.0 ,
              "Vehicle Reaching On_time" :10.0,
              "Reach Hotspot" : 10.0
              }


VEHICLE_COST_PER_KM = {
    'L.M.V. (CAR)': {'PETROL': 10, 'DIESEL': 8.5, 'ELECTRIC(BEV)': 3.3, 'ELECTRIC(BOV)': 4.2, 
                      'PETROL/CNG': 6.7, 'PETROL/LPG': 7.5, 'HYBRID(PHEV)': 5.8, 'HYBRID(HEV)': 5, 'FCEV': 4.2},
    
    'HGV': {'DIESEL': 20.8, 'CNG': 16.6, 'LNG': 15, 'ELECTRIC(BEV)': 8.3, 'ELECTRIC(BOV)': 10, 'FCEV': 7.5, 'HYBRID(HEV)': 12.5},
    
    'SCOOTER/SCOOTERATE': {'PETROL': 5, 'ELECTRIC(BEV)': 1.7, 'ELECTRIC(BOV)': 2.1},
    
    'TWO WHEELER(NT)': {'PETROL': 4.2, 'ELECTRIC(BEV)': 1.7, 'ELECTRIC(BOV)': 2.1},
    
    '2WN': {'PETROL': 4.2, 'ELECTRIC(BEV)': 1.7, 'ELECTRIC(BOV)': 2.1},
    
    '3WT': {'PETROL': 6.7, 'DIESEL': 5.8, 'CNG': 4.2, 'ELECTRIC(BEV)': 2.5, 'ELECTRIC(BOV)': 1.2, 'LPG': 5},
    
    'M-Cycle/Scooter(2WN)': {'PETROL': 4.2, 'ELECTRIC(BEV)': 1.7, 'ELECTRIC(BOV)': 2.1},
    
    'MOTOR CYCLE': {'PETROL': 4.2, 'ELECTRIC(BEV)': 1.7, 'ELECTRIC(BOV)': 2.1},
    
    'LMV': {'PETROL': 10, 'DIESEL': 8.5, 'ELECTRIC(BEV)': 3.3, 'ELECTRIC(BOV)': 4.2, 
            'PETROL/CNG': 6.7, 'PETROL/LPG': 7.5, 'HYBRID(HEV)': 5, 'HYBRID(PHEV)': 5.8},
    
    'BUS': {'DIESEL': 16.6, 'CNG': 15, 'LNG': 13.3, 'ELECTRIC(BEV)': 6.6, 'ELECTRIC(BOV)': 8.3, 'FCEV': 5.8, 'HYBRID(HEV)': 10},
    
    'TRUCK': {'DIESEL': 25, 'CNG': 20.8, 'LNG': 18.3, 'ELECTRIC(BEV)': 10, 'ELECTRIC(BOV)': 11.6, 'FCEV': 8.3},
    
    'TRACTOR': {'DIESEL': 15, 'CNG': 11.6, 'ELECTRIC(BEV)': 5, 'ELECTRIC(BOV)': 5.8},
    
    'PICKUP': {'PETROL': 12.5, 'DIESEL': 10, 'CNG': 8.3, 'LPG': 9.2, 'ELECTRIC(BEV)': 4.2, 'ELECTRIC(BOV)': 5, 'HYBRID(PHEV)': 6.7},
    
    'VAN': {'PETROL': 11.6, 'DIESEL': 10, 'CNG': 8.3, 'LPG': 9.2, 'ELECTRIC(BEV)': 4.2, 'ELECTRIC(BOV)': 5, 'HYBRID(HEV)': 6.7},
    
    'AUTORICKSHAW': {'PETROL': 6.7, 'DIESEL': 5.8, 'CNG': 4.2, 'LPG': 5, 'ELECTRIC(BEV)': 2.5, 'ELECTRIC(BOV)': 2.9},
    
    'MINIBUS': {'DIESEL': 15, 'CNG': 12.5, 'ELECTRIC(BEV)': 5.8, 'ELECTRIC(BOV)': 6.7, 'FCEV': 5, 'HYBRID(HEV)': 8.3},
    
    'SUV': {'PETROL': 11.6, 'DIESEL': 10, 'CNG': 8.3, 'ELECTRIC(BEV)': 4.2, 'ELECTRIC(BOV)': 5, 'HYBRID(HEV)': 5.8, 'FCEV': 5},
    
    'CROSSOVER': {'PETROL': 10.8, 'DIESEL': 9.2, 'ELECTRIC(BEV)': 4.2, 'ELECTRIC(BOV)': 5, 'HYBRID(HEV)': 5.8},
    
    'SEDAN': {'PETROL': 10, 'DIESEL': 8.3, 'ELECTRIC(BEV)': 3.3, 'ELECTRIC(BOV)': 4.2, 'HYBRID(HEV)': 5, 'HYBRID(PHEV)': 5.8},
    
    'HATCHBACK': {'PETROL': 8.3, 'DIESEL': 6.7, 'ELECTRIC(BEV)': 2.5, 'ELECTRIC(BOV)': 3.3, 'HYBRID(HEV)': 4.2},
    
    'COUPE': {'PETROL': 11.6, 'DIESEL': 10, 'ELECTRIC(BEV)': 4.2, 'ELECTRIC(BOV)': 5, 'HYBRID(HEV)': 5.8},
    
    'CONVERTIBLE': {'PETROL': 12.5, 'ELECTRIC(BEV)': 5, 'ELECTRIC(BOV)': 5.8},
    
    'FIRE TRUCK': {'DIESEL': 29.2, 'ELECTRIC(BEV)': 12.5, 'ELECTRIC(BOV)': 15},
    
    'AMBULANCE': {'PETROL': 15, 'DIESEL': 12.5, 'ELECTRIC(BEV)': 5.8, 'ELECTRIC(BOV)': 6.7},
    
    'POLICE VEHICLE': {'PETROL': 13.3, 'DIESEL': 11.6, 'ELECTRIC(BEV)': 5, 'ELECTRIC(BOV)': 5.8},
    
    'MILITARY VEHICLE': {'DIESEL': 33.3, 'ELECTRIC(BEV)': 16.6, 'ELECTRIC(BOV)': 18.3},
    
    'GARBAGE TRUCK': {'DIESEL': 23.3, 'CNG': 18.3, 'ELECTRIC(BEV)': 10, 'ELECTRIC(BOV)': 11.6},
}





