export type DictionaryNamespace = Record<string, string>;

export type Dictionary = {
  common: DictionaryNamespace;
  nav: DictionaryNamespace;
  dashboard: DictionaryNamespace;
  receipts: DictionaryNamespace;
  auth: DictionaryNamespace;
  settings: DictionaryNamespace;
  org: DictionaryNamespace;
  readyToFile: DictionaryNamespace;
  notifications: DictionaryNamespace;
  errors: DictionaryNamespace;
  completeness: DictionaryNamespace;
  household: DictionaryNamespace;
  export: DictionaryNamespace;
  manualReceipt: DictionaryNamespace;
  orgExport: DictionaryNamespace;
  orgBulkImport: DictionaryNamespace;
};

export type DictionaryNamespaceName = keyof Dictionary;
