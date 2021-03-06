# Copyright (C) 2018-present prototyped.cn. All rights reserved.
# Distributed under the terms and conditions of the Apache License.
# See accompanying files LICENSE.

from taksi.importer.excel import ExcelImporter
from taksi.importer.mysql import MySQLImporter

from taksi.generator.cpp.gen_csv_load import CppCsvLoadGenerator
from taksi.generator.csharp.gen_csv_load import CSharpCsvLoadGenerator
from taksi.generator.csharp.gen_json_load import CSharpJsonLoadGenerator
from taksi.generator.java.gen_csv_load import JavaCsvLoadGenerator
from taksi.generator.java.gen_json_load import JavaJsonLoadGenerator
from taksi.generator.go.gen_csv_load import GoCsvLoadGenerator
from taksi.generator.go.gen_json_load import GoJsonLoadGenerator
from taksi.generator.go.gen_sql_orm import GoSqlOrmGenerator

from taksi.datagen.csv import CsvDataGen
from taksi.datagen.json import JsonDataGen

# data importers
importer_registry = {
    ExcelImporter.name(): ExcelImporter(),
    MySQLImporter.name(): MySQLImporter(),
}

# code generators
code_generator_registry = {
    CppCsvLoadGenerator.name(): CppCsvLoadGenerator(),
    CSharpCsvLoadGenerator.name(): CSharpCsvLoadGenerator(),
    CSharpJsonLoadGenerator.name(): CSharpJsonLoadGenerator(),
    JavaCsvLoadGenerator.name(): JavaCsvLoadGenerator(),
    JavaJsonLoadGenerator.name(): JavaJsonLoadGenerator(),
    GoCsvLoadGenerator.name(): GoCsvLoadGenerator(),
    GoJsonLoadGenerator.name(): GoJsonLoadGenerator(),
    GoSqlOrmGenerator.name(): GoSqlOrmGenerator(),
}

# data generators
data_generator_registry = {
    CsvDataGen.name(): CsvDataGen(),
    JsonDataGen.name(): JsonDataGen(),
}


def get_importer(name):
    return importer_registry.get(name, None)


# get code generator by name
def get_code_generator(name):
    return code_generator_registry.get(name, None)


# get data generator by name
def get_data_generator(name):
    return data_generator_registry.get(name, None)
