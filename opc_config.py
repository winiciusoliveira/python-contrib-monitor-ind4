# Mapeamento baseado no clp.ts
# Relaciona o api_id (LOOMxx) com o Endpoint e o NodeID de Running

OPC_MAP = {
	"LOOM01" : {
		"endpoint" : "opc.tcp://10.243.67.30:4840", "node_running" : "ns=2;s=Loom_1.Tags.Tear01TurnOn"
	}, "LOOM02" : {
		"endpoint" : "opc.tcp://10.243.67.5:4840", "node_running" : "ns=2;s=Loom_2.Tags.160_214_1_Loom_02_Running"
	}, "LOOM03" : {
		"endpoint" : "opc.tcp://10.243.67.6:4890", "node_running" : "ns=1;s=1.538.1.0.0.0"
	}, "LOOM04" : {
		"endpoint" : "opc.tcp://10.243.67.7:4840", "node_running" : "ns=2;s=Siemens S7-1200/S7-1500.Tags.Loom04Running"
	}, "LOOM05" : {
		"endpoint" : "opc.tcp://10.243.67.8:4840", "node_running" : "ns=2;s=Siemens S7-1200/S7-1500.Tags.Loom05Running"
	}, "LOOM06" : {
		"endpoint" : "opc.tcp://10.243.67.9:4870", "node_running" : "ns=3;s=Loom06Running"
	}, "LOOM07" : {
		"endpoint" : "opc.tcp://10.243.67.10:4840", "node_running" : "ns=2;s=Loom_CPU414_DP.DB550__loomStatus__LoomOn"
	}, "LOOM08" : {
		"endpoint" : "opc.tcp://10.243.67.14:4870", "node_running" : "ns=3;s=machine running"
	}, "LOOM09" : {
		"endpoint" : "opc.tcp://10.243.67.12:4870", "node_running" : "ns=3;s=Loom09Running"
	}, "LOOM10" : {
		"endpoint" : "opc.tcp://10.243.67.13:4890", "node_running" : "ns=1;s=1.18206.1.0.0.0"
	}, "LOOM13" : {
		"endpoint" : "opc.tcp://10.243.67.16:4840", "node_running" : "ns=2;s=Loom_13.Tags.Q100_1_Loom_13_Running"
	}, "LOOM14" : {
		"endpoint" : "opc.tcp://10.243.67.17:4870", "node_running" : "ns=3;s=Loom14Running"
	}, "LOOM15" : {
		"endpoint" : "opc.tcp://10.243.67.18:4870", "node_running" : "ns=3;s=machine running"
	}, "LOOM18" : {
		"endpoint" : "opc.tcp://10.243.67.21:4818", "node_running" : "ns=3;s=Loom18Running"
	}, "LOOM19" : {
		"endpoint" : "opc.tcp://10.243.67.22:4870", "node_running" : "ns=3;s=Loom19Running"
	}, "LOOM20" : {
		"endpoint" : "opc.tcp://10.243.67.23:4870", "node_running" : "ns=3;s=Loom20Running"
	}
}
