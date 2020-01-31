println "=== CSW validator"
// def response = context.expand('${http-request#Response}');
// String xml = new File('/Users/kentsang/Projects/GDS/docker-ckan/src/2.8/ckanext-datagovuk/bin/csw.xml').text

def get = new URL("https://ckan.publishing.service.gov.uk/csw?request=GetCapabilities&service=CSW&version=2.0.2").openConnection();
def getRC = get.getResponseCode();
String xml = "";
if(getRC.equals(200)) {
    xml = get.getInputStream().getText()
    println(xml);
}

def capabilities = new XmlSlurper().parseText(xml);

println "=== Capabilities"
println capabilities
println "=== End Capabilities"

def extendedCapabilities = capabilities.depthFirst().findAll{it.name() == 'ExtendedCapabilities' && it.parent().name() == 'OperationsMetadata'}[0];
// def extendedCapabilities = capabilities.depthFirst().findAll{it.name() == 'ExtendedCapabilities'}[0];

println "=== extendedCapabilities"
println extendedCapabilities
println "=== end extendedCapabilities"

println "=== extendedCapabilities.MetadataUrl"
println extendedCapabilities.MetadataUrl
println "=== end extendedCapabilities.MetadataUrl"

println "=== extendedCapabilities.ResourceLocator"
println extendedCapabilities.ResourceLocator
println "=== end extendedCapabilities.ResourceLocator"

println "=== serviceIdentification"
def serviceIdentification = capabilities.depthFirst().findAll{it.name() == 'ServiceIdentification'}[0];
println serviceIdentification.Title
println "=== end serviceIdentification"

println "=== end CSW validator"