#!/usr/bin/env python

#
# Standard geni-lib/portal libraries
#
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab as elab
import geni.rspec.igext as IG
import geni.urn as URN


tourDescription = """
Use this profile to instantiate an experiment using Open Air Interface
to realize an end-to-end LTE mobile network. The profile supports two
variants: (i) a simulated RAN (UE and eNodeB) connected to an EPC, or
(ii) an OTS UE (Nexus 5) connected to an SDR-based eNodeB via a
controlled RF attenuator and connected to an EPC.(iii) an OTS UE 
(Nexus 5) connected to 2 RRUs via controlled RF attenuator, RRUs 
would be connected to an SDR-based eNodeB further connected to an EPC.

The simulated version of the profile uses the following resources:

  * A d430 compute node running the OAI simulated UE and eNodeB ('sim-enb') 
  * A d430 compute node running the OAI EPC (HSS, MME, SPGW) ('epc')

The OTS UE/SDR-based eNodeB version of the profile includes
the following resources:

  * Off-the-shelf Nexus 5 UE running Android 4.4.4 KitKat ('rue1')
  * SDR eNodeB (Intel NUC + USRP B210) running OAI eNodeB ('enb1')
  * A d430 compute node running the OAI EPC (HSS, MME, SPGW) ('epc')
  * A d430 compute node providing out-of-band ADB access to the UE ('adb-tgt')

Startup scripts automatically configure OAI for the specific allocated resources.

For more detailed information:

  * [Getting Started](https://gitlab.flux.utah.edu/powder-profiles/OAI-GENERAL/blob/master/README.md)

""";

tourInstructions = """
After your experiment swapped in succesfully (i.e., is in the Ready state):

**For the version with simulated UE and eNodeB**

Log onto the `epc` node and run:

    sudo /local/repository/bin/start_oai.pl -r sim

This will start up the EPC services on the `epc`node *and* the
simulated UE/eNodeB on the `sim-enb` node.

Log onto the `sim-enb` to verify the functionality:

	ping -I oip1 8.8.8.8
	
You can also look at the output of the simulated UE/eNodeB process:

	sudo screen -r sim_enb

**For the version with OTS UE and SDR-based eNodeB**

Log onto the `enb1` node and start the eNodeB service:

	sudo /local/repository/bin/enb.start.sh
	
To view the output of the eNodeB:

	sudo screen -r enb


Log onto the `epc` node and start the EPC services:

	sudo /local/repository/bin/start_oai.pl
	
To log onto the UE (`rue1`), first log onto the `adb-tgt` node and start up the adb daemon:

	pnadb -a

Then (still on `adb-tgt`) get an ADB shell on the UE by running:

	adb shell
	
If the UE successfully connected you should be able to ping an address on
the Internet from the ADB shell, e.g.,

	ping 8.8.8.8
	
If the UE did not connect by itself, (i.e., you get a "Network is unreachable" error),
you might have to reboot the UE (by executing `adb reboot` from the `adb-tgt` node,
or by executing `reboot` directly in the ADB shell on the UE). And then repeating
the `pnadb -a` and `adb shell` commands to get back on the UE to test.


While OAI is still a system in development and may be unstable, you can usually recover
from any issue by running `start_oai.pl` to restart all the services.

  * [More details](https://gitlab.flux.utah.edu/powder-profiles/OAI-GENERAL/blob/master/README.md)

""";


#
# PhantomNet extensions.
#
import geni.rspec.emulab.pnext as PN

#
# Globals
#
class GLOBALS(object):
    OAI_DS = "urn:publicid:IDN+emulab.net:phantomnet+ltdataset+oai-develop"
    OAI_SIM_DS = "urn:publicid:IDN+emulab.net:phantomnet+dataset+PhantomNet:oai"
    UE_IMG  = URN.Image(PN.PNDEFS.PNET_AM, "PhantomNet:ANDROID444-STD")
    ADB_IMG = URN.Image(PN.PNDEFS.PNET_AM, "PhantomNet:UBUNTU14-64-PNTOOLS")
    #OAI_EPC_IMG = URN.Image(PN.PNDEFS.PNET_AM, "PhantomNet:UBUNTU16-64-OAIEPC")
    OAI_EPC_IMG = "urn:publicid:IDN+emulab.net+image+CCIT//OAI-GENERAL-2RRU.epc"
    OAI_ENB_IMG = URN.Image(PN.PNDEFS.PNET_AM, "PhantomNet:OAI-Real-Hardware.enb1")
    OAI_RCC_IMG = "urn:publicid:IDN+emulab.net+image+CCIT//OAI-GENERAL-2RRU.enb1" 
    OAI_RRU1_IMG = "urn:publicid:IDN+emulab.net+image+CCIT//OAI-GENERAL-2RRU.rru1" 
    OAI_RRU2_IMG = "urn:publicid:IDN+emulab.net+image+CCIT//OAI-GENERAL-2RRU.rru2" 
    OAI_SIM_IMG = URN.Image(PN.PNDEFS.PNET_AM, "PhantomNet:UBUNTU14-64-OAI")
    OAI_CONF_SCRIPT = "/usr/bin/sudo /local/repository/bin/config_oai.pl"
    NUC_HWTYPE = "nuc5300"
    UE_HWTYPE = "nexus5"

def connectOAI_DS(node, sim):
    # Create remote read-write clone dataset object bound to OAI dataset
    bs = request.RemoteBlockstore("ds-%s" % node.name, "/opt/oai")
    if sim == 1:
	bs.dataset = GLOBALS.OAI_SIM_DS
    else:
	bs.dataset = GLOBALS.OAI_DS
    bs.rwclone = True

    # Create link from node to OAI dataset rw clone
    node_if = node.addInterface("dsif_%s" % node.name)
    bslink = request.Link("dslink_%s" % node.name)
    bslink.addInterface(node_if)
    bslink.addInterface(bs.interface)
    bslink.vlan_tagging = True
    bslink.best_effort = True

#
# This geni-lib script is designed to run in the PhantomNet Portal.
#
pc = portal.Context()

#
# Profile parameters.
#

sim_hardware_types = ['d430','d740','d710']

pc.defineParameter("TYPE", "Experiment type",
                   portal.ParameterType.STRING,"2RRU",[("sim","Simulated UE/eNodeB"),("1RRU","OTS UE with RF attenuator 1 RRU"),("2RRU","OTS UE with RF attenuator and 2 RRUs")],
                   longDescription="*Simulated RAN*: OAI simulated UE/eNodeB connected to an OAI EPC. *OTS UE/SDR-based eNodeB with RF attenuator connected to OAI EPC*: OTS UE (Nexus 5) connected to controllable RF attenuator matrix.")

pc.defineParameter("FIXED_UE", "Bind to a specific UE",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Input the name of a POWDER controlled RF UE node to allocate (e.g., 'ue1').  Leave blank to let the mapping algorithm choose.")
pc.defineParameter("FIXED_ENB", "Bind to a specific eNodeB",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Input the name of a POWDER controlled RF eNodeB device to allocate (e.g., 'nuc1').  Leave blank to let the mapping algorithm choose.  If you bind both UE and eNodeB devices, mapping will fail unless there is path between them via the attenuator matrix.")
pc.defineParameter("FIXED_RRU1", "Bind to a specific RRU1",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Input the name of a POWDER controlled RF device to allocate (e.g., 'nuc1').  Leave blank to let the mapping algorithm choose.  If you bind both UE and RRU devices, mapping will fail unless there is path between them via the attenuator matrix.")
pc.defineParameter("FIXED_RRU2", "Bind to a specific RRU2",
                   portal.ParameterType.STRING, "", advanced=True,
                   longDescription="Input the name of a POWDER controlled RF device to allocate (e.g., 'nuc1').  Leave blank to let the mapping algorithm choose.  If you bind both UE and RRU devices, mapping will fail unless there is path between them via the attenuator matrix.")

pc.defineParameter("EPC_HWTYPE", "Compute hardware type to use for EPC and ADB-TGT",
                   portal.ParameterType.STRING, sim_hardware_types[0],
                   sim_hardware_types, advanced=True,
                   longDescription="Use this parameter if you would like to select a different hardware type to use for EPC.  The types in this list are known to work.")

pc.defineParameter("SIM_HWTYPE", "Compute hardware type to use (SIM mode only)",
                   portal.ParameterType.STRING, sim_hardware_types[0],
                   sim_hardware_types, advanced=True,
                   longDescription="Use this parameter if you would like to select a different hardware type to use FOR SIMULATED MODE.  The types in this list are known to work.")

params = pc.bindParameters()

#
# Give the library a chance to return nice JSON-formatted exception(s) and/or
# warnings; this might sys.exit().
#
pc.verifyParameters()

#
# Create our in-memory model of the RSpec -- the resources we're going
# to request in our experiment, and their configuration.
#
request = pc.makeRequestRSpec()
epclink = request.Link("s1-lan")

# Checking for oaisim

if params.TYPE == "sim":
    sim_enb = request.RawPC("sim-enb")
    sim_enb.disk_image = GLOBALS.OAI_SIM_IMG
    sim_enb.hardware_type = params.SIM_HWTYPE
    sim_enb.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r SIM_ENB"))
    connectOAI_DS(sim_enb, 1)
    epclink.addNode(sim_enb)
elif params.TYPE == "1RRU":
    # Add a node to act as the ADB target host
    adb_t = request.RawPC("adb-tgt")
    adb_t.disk_image = GLOBALS.ADB_IMG
    adb_t.hardware_type = params.EPC_HWTYPE

    # Add first NUC RRU node.
    rru0 = request.RawPC("rru0")
    if params.FIXED_RRU1:
        rru0.component_id = params.FIXED_RRU1
    rru0.hardware_type = GLOBALS.NUC_HWTYPE
    rru0.disk_image = GLOBALS.OAI_RRU1_IMG
    rru0.Desire( "rf-controlled", 1 )
    connectOAI_DS(rru0, 0)
    rru0.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r ENB"))
    rru0_rue1_rf = rru0.addInterface("rue1_rf")

    # Add a NUC eNB node.
    rcc = request.RawPC("rcc")
    if params.FIXED_ENB:
        rcc.component_id = params.FIXED_ENB
    rcc.hardware_type = GLOBALS.NUC_HWTYPE
    rcc.disk_image = GLOBALS.OAI_RCC_IMG
    rcc.Desire( "rf-controlled", 1 )
    connectOAI_DS(rcc, 0)
    rcc.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r ENB"))
    rcc_epc = rcc.addInterface("epc")

    # Add an OTS (Nexus 5) UE
    rue1 = request.UE("rue1")
    if params.FIXED_UE:
        rue1.component_id = params.FIXED_UE
    rue1.hardware_type = GLOBALS.UE_HWTYPE
    rue1.disk_image = GLOBALS.UE_IMG
    rue1.Desire( "rf-controlled", 1 )    
    rue1.adb_target = "adb-tgt"
    rue1_rru0_rf = rue1.addInterface("enb1_rf")

    # Create the RF link 1 between the Nexus 5 UE and RRU1
    rflink1 = request.RFLink("rflink1")
    rflink1.addInterface(rru0_rue1_rf)
    rflink1.addInterface(rue1_rru0_rf)

    # Add a link connecting RRU1 and the NUC eNB.
    rru0link = request.Link("fhaul-1")
    rru0link.addNode(rru0)  
    rru0link.addNode(rcc)
    rru0link.link_multiplexing = True
    rru0link.vlan_tagging = True
    rru0link.best_effort = True

    # Add a link connecting the NUC eNB and the OAI EPC node.
    epclink.addNode(rcc)
else:
    # Add a node to act as the ADB target host
    adb_t = request.RawPC("adb-tgt")
    adb_t.disk_image = GLOBALS.ADB_IMG
    adb_t.hardware_type = params.EPC_HWTYPE

    # Add first NUC RRU node.
    rru0 = request.RawPC("rru0")
    if params.FIXED_RRU1:
        rru0.component_id = params.FIXED_RRU1
    rru0.hardware_type = GLOBALS.NUC_HWTYPE
    rru0.disk_image = GLOBALS.OAI_RRU1_IMG
    rru0.Desire( "rf-controlled", 1 )
    connectOAI_DS(rru0, 0)
    rru0.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r ENB"))
    rru0_rue1_rf = rru0.addInterface("rue1_rf")
    

    # Add second NUC RRU node.
    rru1 = request.RawPC("rru1")
    if params.FIXED_RRU2:
        rru1.component_id = params.FIXED_RRU2
    rru1.hardware_type = GLOBALS.NUC_HWTYPE
    rru1.disk_image = GLOBALS.OAI_RRU2_IMG
    rru1.Desire( "rf-controlled", 1 )
    connectOAI_DS(rru1, 0)
    rru1.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r ENB"))
    rru1_rue1_rf = rru1.addInterface("rue1_rf")

    # Add a NUC eNB node.
    rcc = request.RawPC("rcc")
    if params.FIXED_ENB:
        rcc.component_id = params.FIXED_ENB
    rcc.hardware_type = GLOBALS.NUC_HWTYPE
    rcc.disk_image = GLOBALS.OAI_RCC_IMG
    rcc.Desire( "rf-controlled", 1 )
    connectOAI_DS(rcc, 0)
    rcc.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r ENB"))
    rcc_epc = rcc.addInterface("epc")

    # Add an OTS (Nexus 5) UE
    rue1 = request.UE("rue1")
    if params.FIXED_UE:
        rue1.component_id = params.FIXED_UE
    rue1.hardware_type = GLOBALS.UE_HWTYPE
    rue1.disk_image = GLOBALS.UE_IMG
    rue1.Desire( "rf-controlled", 1 )    
    rue1.adb_target = "adb-tgt"
    rue1_rru0_rf = rue1.addInterface("rru0_rf")
    rue1_rru1_rf = rue1.addInterface("rru1_rf")


    # Create the RF link 1 between the Nexus 5 UE and RRU1
    rflink1 = request.RFLink("rflink1")
    rflink1.addInterface(rru0_rue1_rf)
    rflink1.addInterface(rue1_rru0_rf)

    # Create the RF link 2 between the Nexus 5 UE and RRU2
    rflink2 = request.RFLink("rflink2")
    rflink2.addInterface(rru1_rue1_rf)
    rflink2.addInterface(rue1_rru1_rf)

    # Add a link connecting RRU1 and the NUC eNB.
    rru0link = request.Link("fhaul-1")
    rru0link.addNode(rru0)  
    rru0link.addNode(rcc)
    rru0link.link_multiplexing = True
    rru0link.vlan_tagging = True
    rru0link.best_effort = True  
    
    # Add a link connecting RRU1 and the NUC eNB.
    rru1link = request.Link("fhaul-2")
    rru1link.addNode(rru1)  
    rru1link.addNode(rcc)
    rru1link.link_multiplexing = True
    rru1link.vlan_tagging = True
    rru1link.best_effort = True      

    # Add a link connecting the NUC eNB and the OAI EPC node.
    epclink.addNode(rcc)    

# Add OAI EPC (HSS, MME, SPGW) node.
epc = request.RawPC("epc")
epc.disk_image = GLOBALS.OAI_EPC_IMG
epc.hardware_type = params.EPC_HWTYPE
epc.addService(rspec.Execute(shell="sh", command=GLOBALS.OAI_CONF_SCRIPT + " -r EPC"))
connectOAI_DS(epc, 0)

epclink.addNode(epc)
epclink.link_multiplexing = True
epclink.vlan_tagging = True
epclink.best_effort = True

tour = IG.Tour()
tour.Description(IG.Tour.MARKDOWN, tourDescription)
tour.Instructions(IG.Tour.MARKDOWN, tourInstructions)
request.addTour(tour)

#
# Print and go!
#
pc.printRequestRSpec(request)
