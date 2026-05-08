# DPP Sample Evaluation Report

## Summary

- **Total URLs**: 16
- **Successfully fetched**: 13
- **Failed**: 3

## By Recommendation

### EXCELLENT (2)

- `opensource_unicc_org_untp-digital-product-passport-v0.3.10.json`: Verifiable Credential with DPP structure
  - URL: https://opensource.unicc.org/11dot2/spec-untp/-/raw/main/website/samples/untp-digital-product-passport-v0.3.10.json
- `test_uncefact_org_untp-dpp-instance-0.6.0.json`: Verifiable Credential with DPP structure
  - URL: https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-instance-0.6.0.json

### GOOD (4)

- `test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json`: Verifiable Credential structure
  - URL: https://test.uncefact.org/vocabulary/untp/dia/DigitalIdentityAnchor-instance-0.6.1.json
- `opensource_unicc_org_untp-digital-facility-record-v0.3.9.json`: Verifiable Credential structure
  - URL: https://opensource.unicc.org/phila/spec-untp/-/raw/main/website/samples/untp-digital-facility-record-v0.3.9.json
- `BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json`: Battery Pass data
  - URL: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-payload.json
- `batterypass_BatteryPassDataModel_GeneralProductInformation-ld.json`: Battery Pass data
  - URL: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-ld.json

### MODERATE (4)

- `eclipse-tractusx_sldt-semantic-models_BatteryPass.json`: DPP-like structure without VC wrapper
  - URL: https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/io.catenax.battery.battery_pass/6.0.0/gen/BatteryPass.json
- `batterypass_BatteryPassDataModel_Circularity-ld.json`: DPP-like structure without VC wrapper
  - URL: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.Circularity/1.2.0/gen/Circularity-ld.json
- `batterypass_BatteryPassDataModel_MaterialComposition-ld.json`: DPP-like structure without VC wrapper
  - URL: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-ld.json
- `nfc-forum_org_long-dpp-example.json`: DPP-like structure without VC wrapper
  - URL: https://nfc-forum.org/ndpp/long-dpp-example.json

### MAYBE (3)

- `untp-verifiable-credentials_s3_amazonaws_com_bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json`: JSON-LD but structure unclear
  - URL: https://untp-verifiable-credentials.s3.amazonaws.com/bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json
- `schemas_testing_breathable-t-shirt.json`: JSON-LD but structure unclear
  - URL: https://spherity.github.io/schemas/testing/breathable-t-shirt.json
- `batterypass_BatteryPassDataModel_CarbonFootprintForBatteries-ld.json`: JSON-LD but structure unclear
  - URL: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-ld.json

### FAILED (3)

- `zenodo_org_untp-dpp-instance-0.5.0-computer.json`: Invalid JSON: Expecting value: line 2 column 1 (char 1)
  - URL: https://zenodo.org/records/15279026/preview/untp-dpp-instance-0.5.0-computer.json.txt
- `BatteryPassDataModel_BatteryPass_CarbonFootprintForBatteries-payload.json`: Invalid JSON: Expecting value: line 1 column 1 (char 0)
  - URL: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-payload.json
- `BatteryPassDataModel_BatteryPass_MaterialComposition-payload.json`: Invalid JSON: Expecting value: line 1 column 1 (char 0)
  - URL: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-payload.json

## Detailed Evaluation

### untp-verifiable-credentials_s3_amazonaws_com_bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json

- **URL**: https://untp-verifiable-credentials.s3.amazonaws.com/bc075c5f-2304-4b3f-bb24-46d9fa9a8e60.json
- **Hash**: 7fdae740e64218ab
- **Recommendation**: maybe
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: False
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: EnvelopedVerifiableCredential
- **Top keys**: @context, type, id
- **Notes**: JSON-LD but structure unclear

### schemas_testing_breathable-t-shirt.json

- **URL**: https://spherity.github.io/schemas/testing/breathable-t-shirt.json
- **Hash**: f5132472ac04920b
- **Recommendation**: maybe
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: False
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: @context
- **Notes**: JSON-LD but structure unclear

### eclipse-tractusx_sldt-semantic-models_BatteryPass.json

- **URL**: https://raw.githubusercontent.com/eclipse-tractusx/sldt-semantic-models/main/io.catenax.battery.battery_pass/6.0.0/gen/BatteryPass.json
- **Hash**: 50afbb8d50f3be29
- **Recommendation**: moderate
- **Is JSON-LD**: False
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: characteristics, metadata, commercial, identification, performance, sources, materials, safety, handling, conformity
- **Notes**: DPP-like structure without VC wrapper

### zenodo_org_untp-dpp-instance-0.5.0-computer.json

- **URL**: https://zenodo.org/records/15279026/preview/untp-dpp-instance-0.5.0-computer.json.txt
- **Error**: Invalid JSON: Expecting value: line 2 column 1 (char 1)

### test_uncefact_org_DigitalIdentityAnchor-instance-0.6.1.json

- **URL**: https://test.uncefact.org/vocabulary/untp/dia/DigitalIdentityAnchor-instance-0.6.1.json
- **Hash**: 6784faa60f59cb76
- **Recommendation**: good
- **Is JSON-LD**: True
- **Is VC**: True
- **Is DPP-like**: False
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: ['DigitalIdentityAnchor', 'VerifiableCredential']
- **Top keys**: type, @context, id, issuer, validFrom, validUntil, credentialSubject
- **Notes**: Verifiable Credential structure

### opensource_unicc_org_untp-digital-facility-record-v0.3.9.json

- **URL**: https://opensource.unicc.org/phila/spec-untp/-/raw/main/website/samples/untp-digital-facility-record-v0.3.9.json
- **Hash**: 5a6025ab1335864f
- **Recommendation**: good
- **Is JSON-LD**: True
- **Is VC**: True
- **Is DPP-like**: False
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: ['DigitalFacilityRecord', 'VerifiableCredential']
- **Top keys**: type, @context, id, issuer, validFrom, validUntil, credentialSubject
- **Notes**: Verifiable Credential structure

### opensource_unicc_org_untp-digital-product-passport-v0.3.10.json

- **URL**: https://opensource.unicc.org/11dot2/spec-untp/-/raw/main/website/samples/untp-digital-product-passport-v0.3.10.json
- **Hash**: 5b112fea72fc74b6
- **Recommendation**: excellent
- **Is JSON-LD**: True
- **Is VC**: True
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: ['DigitalProductPassport', 'VerifiableCredential']
- **Top keys**: type, @context, id, issuer, validFrom, validUntil, credentialSubject
- **Notes**: Verifiable Credential with DPP structure

### test_uncefact_org_untp-dpp-instance-0.6.0.json

- **URL**: https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-instance-0.6.0.json
- **Hash**: dceb94862b90bce6
- **Recommendation**: excellent
- **Is JSON-LD**: True
- **Is VC**: True
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: ['DigitalProductPassport', 'VerifiableCredential']
- **Top keys**: type, @context, id, issuer, validFrom, validUntil, credentialSubject
- **Notes**: Verifiable Credential with DPP structure

### BatteryPassDataModel_BatteryPass_GeneralProductInformation-payload.json

- **URL**: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-payload.json
- **Hash**: d9d8393364648ed9
- **Recommendation**: good
- **Is JSON-LD**: False
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: True
- **Is Schema**: False
- **Type**: None
- **Top keys**: batteryCategory, operatorInformation, productIdentifier, batteryStatus, puttingIntoService, batteryMass, manufacturingDate, batteryPassportIdentifier, warrentyPeriod, manufacturerInformation
- **Notes**: Battery Pass data

### BatteryPassDataModel_BatteryPass_CarbonFootprintForBatteries-payload.json

- **URL**: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-payload.json
- **Error**: Invalid JSON: Expecting value: line 1 column 1 (char 0)

### batterypass_BatteryPassDataModel_GeneralProductInformation-ld.json

- **URL**: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.GeneralProductInformation/1.2.0/gen/GeneralProductInformation-ld.json
- **Hash**: df821e9ad855ca75
- **Recommendation**: good
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: True
- **Is Schema**: False
- **Type**: None
- **Top keys**: @graph, @context
- **Notes**: Battery Pass data

### batterypass_BatteryPassDataModel_CarbonFootprintForBatteries-ld.json

- **URL**: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.CarbonFootprint/1.2.0/gen/CarbonFootprintForBatteries-ld.json
- **Hash**: ebcb4870f6fd59e2
- **Recommendation**: maybe
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: False
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: @graph, @context
- **Notes**: JSON-LD but structure unclear

### batterypass_BatteryPassDataModel_Circularity-ld.json

- **URL**: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.Circularity/1.2.0/gen/Circularity-ld.json
- **Hash**: bcb5d1e4c3e1822b
- **Recommendation**: moderate
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: @graph, @context
- **Notes**: DPP-like structure without VC wrapper

### batterypass_BatteryPassDataModel_MaterialComposition-ld.json

- **URL**: https://raw.githubusercontent.com/batterypass/BatteryPassDataModel/refs/heads/main/BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-ld.json
- **Hash**: e0692ea9b1f7a837
- **Recommendation**: moderate
- **Is JSON-LD**: True
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: @graph, @context
- **Notes**: DPP-like structure without VC wrapper

### nfc-forum_org_long-dpp-example.json

- **URL**: https://nfc-forum.org/ndpp/long-dpp-example.json
- **Hash**: 57c0c2ed05527cd0
- **Recommendation**: moderate
- **Is JSON-LD**: False
- **Is VC**: False
- **Is DPP-like**: True
- **Is Battery Pass**: False
- **Is Schema**: False
- **Type**: None
- **Top keys**: productID, productName, manufacturer, productionDate, expiryDate, materials, environmentalImpact, compliance, endOfLifeInstructions, digitalPassportLink
- **Notes**: DPP-like structure without VC wrapper

### BatteryPassDataModel_BatteryPass_MaterialComposition-payload.json

- **URL**: https://batterypass.github.io/BatteryPassDataModel/BatteryPass/io.BatteryPass.MaterialComposition/1.2.0/gen/MaterialComposition-payload.json
- **Error**: Invalid JSON: Expecting value: line 1 column 1 (char 0)
