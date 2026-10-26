"""Fixed topic split and literal system strings. No implicit default insertion."""
SYSTEMS={'S0':'','S1':'You are a helpful assistant.','S2':'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.','S3':'The window is open.'}
ALPHAS=[0.,.3,1.,2.]
TARGETS=[3554,30625]
CONTROLS=[401,2219] # semicolon + two newlines; exclamation + two newlines
TOPICS=[
('E01','how a lighthouse helps ships navigate safely near a coast'),
('E02','how paper is collected and processed for recycling'),
('E03','how a greenhouse helps plants grow in cool weather'),
('E04','how a museum prepares an exhibition of fragile objects'),
('E05','how a simple rechargeable battery stores and releases energy'),
('E06','how a town prepares for a local outdoor music festival'),
('E07','how a parcel travels through a sorting depot to its destination'),
('E08','how a potter makes a clay bowl and fires it in a kiln'),
('E09','how a weather station collects and reports measurements'),
('E10','how a small theater prepares a stage for a performance'),
('E11','how a beekeeper checks a hive during the growing season'),
('E12','how an elevator carries people between floors safely'),
('E13','how a harbor team guides a large ship to its berth'),
('E14','how a camera lens brings a scene into focus'),
('E15','how a household can prepare for a planned power outage'),
('E16','how a seed bank preserves samples for future use'),
('E17','how a radio station produces a live morning program'),
('E18','how a team restores a damaged historical photograph'),
('E19','how a bakery schedules several batches of pastries'),
('E20','how a wildlife reserve monitors animal populations'),
('V01','how an aquarium maintains water quality in a large tank'),
('V02','how a book is bound after its pages are printed'),
('V03','how a mountain rescue team organizes a routine training exercise'),
('V04','how a water treatment plant makes river water suitable for drinking'),
('V05','how a choir prepares to sing a new piece of music'),
('V06','how a geologist identifies minerals in a rock sample'),
('V07','how a cable car moves passengers up a hillside'),
('V08','how a conservation team protects a nesting beach'),
('V09','how a ceramic water filter removes some impurities'),
('V10','how a planetarium presents the night sky to visitors'),
('V11','how a small farm organizes the harvest of ripe fruit'),
('V12','how a tailor measures and adjusts a jacket'),
('V13','how a wind turbine converts moving air into electricity'),
('V14','how a dance company plans a touring performance'),
('V15','how a navigation satellite helps a receiver estimate its location'),
('V16','how an archive digitizes and catalogs old letters'),
('V17','how a repair cafe organizes volunteer help for visitors'),
('V18','how a canal lock raises or lowers a boat'),
('V19','how a telescope observatory schedules observations'),
('V20','how a grocery store keeps fresh produce in good condition')]
VARIANT_INSTRUCTIONS=['Present this clearly for a general audience.','Describe this clearly for a general audience.']
MATERIAL=['Here is a clear explanation of the topic. The following account describes the main stages in ordinary language and connects each stage to the next.','A simple explanation of this topic follows. This account describes the main stages using ordinary language and connects each stage to the next.']
POSITION_CONDITIONS=[('none',0),('assistant',8),('assistant',15),('user',8),('user',15)]
def task(topic):return 'Write an informative explanation of '+topic+'. Use three short paragraphs, about 180 words in total. Focus on the requested topic.'
