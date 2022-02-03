local NutkickerCallbacks = {}

function NutkickerCallbacks.onSimulationStart()

	
	log.write('Nutkicker', log.INFO, "Motion export started") 
	
	package.path  = package.path..";"..lfs.currentdir().."/LuaSocket/?.lua"
	package.cpath = package.cpath..";"..lfs.currentdir().."/LuaSocket/?.dll"

	socket = require("socket")
	IPAddress = "127.0.0.1" -- localhost
	--IPAddress = "192.168.178.63" -- Dedicated Laptop
	--IPAddress = "192.168.178.70" -- Simulator
	--IPAddress = "192.168.178.56" -- MacBook Pro
	PortS = 31090

	--Nutkicker_socket = socket.try(socket.connect(IPAddress, PortS))
	--Nutkicker_socket:setoption("tcp-nodelay",true) 
    --log.write('Nutkicker', log.INFO, "Socket connected") 
	Nutkicker_socket = socket.udp()
    log.write('Nutkicker', log.INFO, "Socket created") 
    
	NMC_Counter = 0
end

function NutkickerCallbacks.onSimulationFrame()
	
	--Airdata:
		local NMC_IAS = Export.LoGetIndicatedAirSpeed()
		local NMC_Machnumber = Export.LoGetMachNumber()
		local NMC_TAS = Export.LoGetTrueAirSpeed()
		local vv = Export.LoGetVectorVelocity()
		local NMC_GS = math.sqrt( math.pow(vv.x,2) + math.pow(vv.z,2))
		local NMC_AOA = Export.LoGetAngleOfAttack();
		local NMC_VerticalSpeed = Export.LoGetVerticalVelocity()
		local NMC_Height = Export.LoGetAltitudeAboveGroundLevel()

	--Euler angles:
		local mySelf = Export.LoGetSelfData()
		--local ADI_pitch, ADI_bank, ADI_yaw = LoGetADIPitchBankYaw()
		local NMC_inertial_Yaw = 	mySelf.Heading
		local NMC_inertial_Pitch = 	mySelf.Pitch
		local NMC_inertial_Bank = 	mySelf.Bank

	--Angular rates:
		local NMC_Omega = Export.LoGetAngularVelocity()

	--Accelerations:
		local NMC_Accel = Export.LoGetAccelerationUnits()

	--Metadata:
		local NMC_Time = Export.LoGetModelTime()
		NMC_Counter = NMC_Counter + 1
	
	--Here the data is being sent to the Nutkicker Software: 
	--socket.try(Nutkicker_socket:send(string.format("%.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f  \n",		
    local msg = string.format("%.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f, %.4f  \n",		

													NMC_IAS,					--Airdata[0]
													NMC_Machnumber,				--Airdata[1]
													NMC_TAS,					--Airdata[2]
													NMC_GS,						--Airdata[3]
													NMC_AOA,					--Airdata[4]
													NMC_VerticalSpeed,			--Airdata[5]
													NMC_Height,					--Airdata[6]
													NMC_inertial_Bank,			--Euler[0]
													NMC_inertial_Yaw,			--Euler[1]
													NMC_inertial_Pitch,			--Euler[2]
													NMC_Omega.x,				--Rates[0]
													NMC_Omega.y,				--Rates[1]
													NMC_Omega.z,				--Rates[2]
													NMC_Accel.x,				--Accel[0]
													NMC_Accel.y,				--Accel[1]
													NMC_Accel.z,				--Accel[2]
													NMC_Time,					--Meta[0]
													NMC_Counter					--Meta[1]
																							)
    --                                                                                       )) 
    if Nutkicker_socket then     
       Nutkicker_socket:sendto(msg, IPAddress, PortS)
    end
	
end

function NutkickerCallbacks.onSimulationStop()

	if Nutkicker_socket then 
		-- socket.try(Nutkicker_socket:send("exit")) -- closing the socket
		-- Nutkicker_socket:close()
        Nutkicker_socket = nil
	end
end

DCS.setUserCallbacks(NutkickerCallbacks)