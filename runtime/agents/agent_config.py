#!/usr/bin/env python
"""
agent_cfg.py

This file provides list of input options including:
    name of input, file to execute on remote PC, file to import on platform_controller

    Each pc is sent a startup msg as:  "STARTUP,agent name, agent to import and run"
    An agent_startup.py file on each pc maps agent name to sim executable to run
    The pc starts the sim and then runs the given agent to communicate with the agetn proxy on the platform controller
"""

from collections import namedtuple

AgentDefs = namedtuple('AgentDefs', ['sim_name', # key for this agent, used at Vr pc to lookup executable file path to run
                                     'agent_module', # python agent module to import and run on Vr PC running sim
                                     'agent_gui']) # python agent gui module imported and used by platform controller

AgentStartupMsg = namedtuple('AgentMsg', [
                             'sim_name', # key used by remote PC startup to lookup executable file path to run
                             'agent_module', # python agent module to import and run on PC running sim
                             'ip_addr',  # ip address of controlller pc (Vr pc sends events to this address) 
                             'event_port', # port for above
                             'agent_id']) # the id that identifies this agent instance to the proxy 
                                  

class AgentCfg():
    def __init__(self):
        self.agents = []
        # note the GUI supports up to four agents
        #                              sim  name,        agent module on Vr pc                agent gui on controller po   
        self.agents.append(AgentDefs('space_coaster', 'agents.space_coaster/space_coaster', 'agents.space_coaster.space_coaster_gui'))
        self.agents.append(AgentDefs('nolimits_coaster', 'agents.nolimits_coaster/nolimits_coaster', 'agents.nolimits_coaster.nolimits_coaster_gui'))
        # cfg.agents.append(AgentDefs('MS Flight Simulator', 'NONE', 'NONE'))
        self.agents.append(AgentDefs('Test_agent', 'NONE', 'agents.test_agent.test_agent_gui' ))

        self.default = 1  # the default agent to select in startup dialog


if __name__ == "__main__":
    #  only used for testing
    cfg = AgentCfg()
    # print(cfg.agents)
    for agent in cfg.agents:
        print("name:", agent.sim_name)
        print("module=", agent.agent_module)
        print("gui module=", agent.agent_gui)
        print()
    print("default selection is", cfg.agents[cfg.default].sim_name)
