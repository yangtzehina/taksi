# Copyright (C) 2018-present prototyped.cn. All rights reserved.
# Distributed under the terms and conditions of the Apache License.
# See accompanying files LICENSE.

import os
import taksi.descriptor.types as types
import taksi.descriptor.predef as predef
import taksi.descriptor.lang as lang
import taksi.descriptor.strutil as strutil
import taksi.generator.genutil as genutil
import taksi.version as version
from taksi.generator.csharp.gen_struct import CSharpStructGenerator


CSHARP_METHOD_TEMPLATE = """
    public delegate void ContentReader(string filepath, Action<string> cb);
    
    public static ContentReader reader = ReadFileContent;
    
    public static bool ParseBool(string text)
    {
        if (text.Length > 0)
        {
            return string.Equals(text, "1") ||
                string.Equals(text, "on", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(text, "yes", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(text, "true", StringComparison.OrdinalIgnoreCase);
        }
        return false;
    }
        
    public static List<string> ReadTextToLines(string content)
    {
        List<string> lines = new List<string>();
        using (StringReader reader = new StringReader(content))
        {
            string line;
            while ((line = reader.ReadLine()) != null)
            {
                lines.Add(line);
            }
        }
        return lines;
    }
    
    public static void ReadFileContent(string filepath, Action<string> cb)
    {
        StreamReader reader = new StreamReader(filepath);
        var content = reader.ReadToEnd();
        cb(content);
    }
    
"""


# C# csv load generator
class CSharpCsvLoadGenerator(CSharpStructGenerator):
    TAB_SPACE = '    '

    @staticmethod
    def name():
        return "cs-csv"

    def get_data_member_name(self, name):
        return name + 'Data'

    # 字段比较
    def gen_equal_stmt(self, prefix, struct, key):
        keys = genutil.get_struct_keys(struct, key, lang.map_cs_type)
        args = []
        for tpl in keys:
            args.append('%s%s == %s' % (prefix, tpl[1], tpl[1]))
        return ' && '.join(args)

    # 生成赋值方法
    def gen_field_assgin_stmt(self, name, typename, valuetext, tabs):
        content = ''
        space = self.TAB_SPACE * tabs
        if typename.lower() == 'string':
            content += '%s%s = %s.Trim();\n' % (space, name, valuetext)
        elif typename.lower().find('bool') >= 0:
            content += '%s%s = %s.ParseBool(%s);\n' % (space, name, strutil.config_manager_name, valuetext)
        else:
            content += '%s%s = %s.Parse(%s);\n' % (space, name, typename, valuetext)
        return content

    # 生成array赋值
    def gen_field_array_assign_stmt(self, prefix, typename, name, row_name, array_delim, tabs):
        assert len(array_delim) == 1
        array_delim = array_delim.strip()
        if array_delim == '\\':
            array_delim = '\\\\'

        content = ''
        space = self.TAB_SPACE * tabs
        elem_type = types.array_element_type(typename)
        elem_type = lang.map_cs_type(elem_type)
        content += "%svar items = %s.Split(new char[]{'%s'}, StringSplitOptions.RemoveEmptyEntries);\n" % (space, row_name, array_delim)
        content += '%s%s%s = new %s[items.Length];\n' % (space, prefix, name, elem_type)
        content += "%sfor(int i = 0; i < items.Length; i++) {\n" % space
        content += self.gen_field_assgin_stmt('var value', elem_type, 'items[i]', tabs + 1)
        content += '%s    %s%s[i] = value;\n' % (space, prefix, name)
        content += '%s}\n' % space
        return content

    # 生成map赋值
    def gen_field_map_assign_stmt(self, prefix, typename, name, row_name, map_delims, tabs):
        assert len(map_delims) == 2, map_delims
        delim1 = map_delims[0].strip()
        if delim1 == '\\':
            delim1 = '\\\\'
        delim2 = map_delims[1].strip()
        if delim2 == '\\':
            delim2 = '\\\\'

        space = self.TAB_SPACE * tabs
        k, v = types.map_key_value_types(typename)
        key_type = lang.map_cs_type(k)
        val_type = lang.map_cs_type(v)

        content = "%svar items = %s.Split(new char[]{'%s'}, StringSplitOptions.RemoveEmptyEntries);\n" % (space, row_name, delim1)
        content += '%s%s%s = new Dictionary<%s,%s>();\n' % (space, prefix, name, key_type, val_type)
        content += "%sforeach(string text in items) {\n" % space
        content += '%s    if (text.Length == 0) {\n' % space
        content += '%s        continue;\n' % space
        content += '%s    }\n' % space
        content += "%s    var item = text.Split(new char[]{'%s'}, StringSplitOptions.RemoveEmptyEntries);\n" % (space, delim2)
        content += self.gen_field_assgin_stmt('var key', key_type, 'item[0]', tabs+1)
        content += self.gen_field_assgin_stmt('var value', val_type, 'item[1]', tabs + 1)
        content += '%s    %s%s[key] = value;\n' % (space, prefix, name)
        content += '%s}\n' % space
        return content

    # 生成KV模式的Parse方法
    def gen_kv_parse_method(self, struct):
        rows = struct['data_rows']
        keycol = struct['options'][predef.PredefKeyColumn]
        valcol = struct['options'][predef.PredefValueColumn]
        typcol = int(struct['options'][predef.PredefValueTypeColumn])
        assert keycol > 0 and valcol > 0 and typcol > 0

        keyidx, keyfield = genutil.get_field_by_column_index(struct, keycol)
        validx, valfield = genutil.get_field_by_column_index(struct, valcol)
        typeidx, typefield = genutil.get_field_by_column_index(struct, typcol)

        array_delim = struct['options'].get(predef.OptionArrayDelimeter, predef.DefaultArrayDelimiter)
        map_delims = struct['options'].get(predef.OptionMapDelimeters, predef.DefaultMapDelimiters)

        content = ''
        content += '%s// parse object fields from text rows\n' % self.TAB_SPACE
        content += '%spublic void ParseFromRows(string[][] rows)\n' % self.TAB_SPACE
        content += '%s{\n' % self.TAB_SPACE
        content += '%sif (rows.Length < %d) {\n' % (self.TAB_SPACE*2, len(rows))
        content += '%sthrow new ArgumentException(string.Format("%s: row length out of index, {0} < %d", rows.Length));\n' % (
            self.TAB_SPACE*3, struct['name'], len(rows))
        content += '%s}\n' % (self.TAB_SPACE*2)

        idx = 0
        prefix = 'this.'
        for row in rows:
            name = rows[idx][keyidx].strip()
            name = strutil.camel_case(name)
            origin_typename = rows[idx][typeidx].strip()
            typename = lang.map_cs_type(origin_typename)
            valuetext = 'rows[%d][%d]' % (idx, validx)
            # print('kv', name, origin_typename, valuetext)
            if origin_typename.startswith('array'):
                content += '%s{\n' % (self.TAB_SPACE * 2)
                content += self.gen_field_array_assign_stmt(prefix, origin_typename, name, valuetext, array_delim, 3)
                content += '%s}\n' % (self.TAB_SPACE * 2)
            elif origin_typename.startswith('map'):
                content += '%s{\n' % (self.TAB_SPACE * 2)
                content += self.gen_field_map_assign_stmt(prefix, origin_typename, name, valuetext, map_delims, 3)
                content += '%s}\n' % (self.TAB_SPACE * 2)
            else:
                content += '%sif (rows[%d][%d].Length > 0) {\n' % (self.TAB_SPACE * 2, idx, validx)
                content += self.gen_field_assgin_stmt(prefix + name, typename, valuetext, 3)
                content += '%s}\n' % (self.TAB_SPACE*2)
            idx += 1
        content += '%s}\n\n' % self.TAB_SPACE
        return content

    # 生成ParseFromRow方法
    def gen_parse_method(self, struct):
        content = ''
        if struct['options'][predef.PredefParseKVMode]:
            return self.gen_kv_parse_method(struct)

        array_delim = struct['options'].get(predef.OptionArrayDelimeter, predef.DefaultArrayDelimiter)
        map_delims = struct['options'].get(predef.OptionMapDelimeters, predef.DefaultMapDelimiters)

        vec_idx = 0
        vec_names, vec_name = genutil.get_vec_field_range(struct)

        inner_class_done = False
        inner_field_names, inner_fields = genutil.get_inner_class_mapped_fields(struct)

        content += '%s// parse object fields from a text row\n' % self.TAB_SPACE
        content += '%spublic void ParseFromRow(string[] row)\n' % self.TAB_SPACE
        content += '%s{\n' % self.TAB_SPACE
        content += '%sif (row.Length < %d) {\n' % (self.TAB_SPACE*2, len(struct['fields']))
        content += '%sthrow new ArgumentException(string.Format("%s: row length out of index {0}", row.Length));\n' % (
            self.TAB_SPACE * 3, struct['name'])
        content += '%s}\n' % (self.TAB_SPACE*2)

        idx = 0
        prefix = 'this.'
        for field in struct['fields']:
            field_name = field['name']
            if field_name in inner_field_names:
                if not inner_class_done:
                    inner_class_done = True
                    content += self.gen_cs_inner_class_assign(struct, prefix)
            else:
                origin_type_name = field['original_type_name']
                typename = lang.map_cs_type(origin_type_name)
                valuetext = 'row[%d]' % idx
                if origin_type_name.startswith('array'):
                    content += '%s{\n' % (self.TAB_SPACE * 2)
                    content += self.gen_field_array_assign_stmt(prefix, origin_type_name, field_name, valuetext, array_delim, 3)
                    content += '%s}\n' % (self.TAB_SPACE * 2)
                elif origin_type_name.startswith('map'):
                    content += '%s{\n' % (self.TAB_SPACE * 2)
                    content += self.gen_field_map_assign_stmt(prefix, origin_type_name, field_name, valuetext, map_delims, 3)
                    content += '%s}\n' % (self.TAB_SPACE * 2)
                else:
                    content += '%sif (row[%d].Length > 0) {\n' % (self.TAB_SPACE * 2, idx)
                    if field_name in vec_names:
                        name = '%s[%d]' % (vec_name, vec_idx)
                        content += self.gen_field_assgin_stmt(prefix+name, typename, valuetext, 3)
                        vec_idx += 1
                    else:
                        content += self.gen_field_assgin_stmt(prefix+field_name, typename, valuetext, 3)
                    content += '%s}\n' % (self.TAB_SPACE*2)
            idx += 1
        content += '%s}\n\n' % self.TAB_SPACE
        return content

    # 生成内部类的parse
    def gen_cs_inner_class_assign(self, struct, prefix):
        content = ''
        inner_class_type = struct["options"][predef.PredefInnerTypeClass]
        inner_var_name = struct["options"][predef.PredefInnerTypeName]
        inner_fields = genutil.get_inner_class_struct_fields(struct)
        start, end, step = genutil.get_inner_class_range(struct)
        assert start > 0 and end > 0 and step > 1
        content += '        %s%s = new %s[%d];\n' % (prefix, inner_var_name, inner_class_type, (end-start)/step)
        content += '        for (int i = %s, j = 0; i < %s; i += %s, j++) \n' % (start, end, step)
        content += '        {\n'
        content += '            %s item = new %s();\n' % (inner_class_type, inner_class_type)
        for n in range(step):
            field = inner_fields[n]
            origin_type = field['original_type_name']
            typename = lang.map_cs_type(origin_type)
            valuetext = 'row[i + %d]' % n
            content += '            if (row[i + %d].Length > 0) \n' % n
            content += '            {\n'
            content += self.gen_field_assgin_stmt("item." + field['name'], typename, valuetext, 4)
            content += '            }\n'
        content += '            %s%s[j] = item;\n' % (prefix, inner_var_name)
        content += '        }\n'
        return content

    #
    def gen_static_data(self, struct):
        content = '\n'
        if struct['options'][predef.PredefParseKVMode]:
            content += '    public static %s Instance { get; private set; }\n\n' % struct['name']
        else:
            content += '    public static %s[] Data { get; private set; } \n\n' % struct['name']

        return content

    def gen_kv_struct_load_method(self, struct):
        rows = struct['data_rows']
        keycol = struct['options'][predef.PredefKeyColumn]
        valcol = struct['options'][predef.PredefValueColumn]
        typcol = int(struct['options'][predef.PredefValueTypeColumn])
        assert keycol > 0 and valcol > 0 and typcol > 0

        content = '%spublic static void LoadFromLines(List<string> lines)\n' % self.TAB_SPACE
        content += '%s{\n' % self.TAB_SPACE
        content += '%svar rows = new string[lines.Count][];\n' % (self.TAB_SPACE * 2)
        content += '%sfor(int i = 0; i < lines.Count; i++)\n' % (self.TAB_SPACE*2)
        content += '%s{\n' % (self.TAB_SPACE*2)
        content += '%sstring line = lines[i];\n' % (self.TAB_SPACE * 3)
        content += "%srows[i] = line.Split(',');\n" % (self.TAB_SPACE*3)
        content += '%s}\n' % (self.TAB_SPACE*2)
        content += '%sInstance = new %s();\n' % (self.TAB_SPACE * 2, struct['name'])
        content += '%sInstance.ParseFromRows(rows);\n' % (self.TAB_SPACE * 2)
        content += '%s}\n\n' % self.TAB_SPACE
        return content

    # 生成Load方法
    def gen_load_method(self, struct):
        if struct['options'][predef.PredefParseKVMode]:
            return self.gen_kv_struct_load_method(struct)

        content = ''
        content = '%spublic static void LoadFromLines(List<string> lines)\n' % self.TAB_SPACE
        content += '%s{\n' % self.TAB_SPACE
        content += '%svar list = new %s[lines.Count];\n' % (self.TAB_SPACE * 2, struct['name'])
        content += '%sfor(int i = 0; i < lines.Count; i++)\n' % (self.TAB_SPACE * 2)
        content += '%s{\n' % (self.TAB_SPACE * 2)
        content += '%sstring line = lines[i];\n' % (self.TAB_SPACE * 3)
        content += "%svar row = line.Split(',');\n" % (self.TAB_SPACE * 3)
        content += '%svar obj = new %s();\n' % (self.TAB_SPACE * 3, struct['name'])
        content += "%sobj.ParseFromRow(row);\n" % (self.TAB_SPACE * 3)
        content += "%slist[i] = obj;\n" % (self.TAB_SPACE * 3)
        content += '%s}\n' % (self.TAB_SPACE * 2)
        content += '%sData = list;\n' % (self.TAB_SPACE * 2)
        content += '%s}\n\n' % self.TAB_SPACE
        return content

    # 生成Get()方法
    def gen_get_method(self, struct):
        if struct['options'][predef.PredefParseKVMode]:
            return ''

        keys = genutil.get_struct_keys(struct, predef.PredefGetMethodKeys, lang.map_cs_type)
        if len(keys) == 0:
            return ''

        formal_param = []
        arg_names = []
        for tpl in keys:
            typename = tpl[0]
            formal_param.append('%s %s' % (typename, tpl[1]))
            arg_names.append(tpl[1])

        content = ''
        content += '    // get an item by key\n'
        content += '    public static %s Get(%s)\n' % (struct['name'], ', '.join(formal_param))
        content += '    {\n'
        content += '        foreach (%s item in Data)\n' % struct['name']
        content += '        {\n'
        content += '            if (%s)\n' % self.gen_equal_stmt('item.', struct, 'get-keys')
        content += '            {\n'
        content += '                return item;\n'
        content += '            }\n'
        content += '        }\n'
        content += '        return null;\n'
        content += '    }\n\n'
        return content

    # 生成GetRange()方法
    def gen_range_method(self, struct):
        if struct['options'][predef.PredefParseKVMode]:
            return ''

        if predef.PredefRangeMethodKeys not in struct['options']:
            return ''

        keys = genutil.get_struct_keys(struct, predef.PredefRangeMethodKeys, lang.map_cs_type)
        assert len(keys) > 0

        formal_param = []
        params = []
        arg_names = []
        for tpl in keys:
            typename = tpl[0]
            formal_param.append('%s %s' % (typename, tpl[1]))
            arg_names.append(tpl[1])

        content = ''
        content += '    // get a range of items by key\n'
        content += '    public static List<%s> GetRange(%s)\n' % (struct['name'], ', '.join(formal_param))
        content += '    {\n'
        content += '        var range = new List<%s>();\n' % struct['name']
        content += '        foreach (%s item in Data)\n' % struct['name']
        content += '        {\n'
        content += '            if (%s)\n' % self.gen_equal_stmt('item.', struct, 'range-keys')
        content += '            {\n'
        content += '                range.Add(item);\n'
        content += '            }\n'
        content += '        }\n'
        content += '        return range;\n'
        content += '    }\n\n'
        return content

    # 生成manager类型
    def gen_global_class(self, descriptors):
        content = ''
        content += 'public class %s\n{\n' % strutil.config_manager_name
        content += CSHARP_METHOD_TEMPLATE
        content += '    public static void LoadAllConfig(Action completeFunc) \n'
        content += '    {\n'
        for i in range(len(descriptors)):
            struct = descriptors[i]
            name = strutil.camel_to_snake(struct['name'])
            content += '        reader("%s.csv", (content) =>\n' % name
            content += '        {\n'
            content += '            var lines = ReadTextToLines(content);\n'
            content += '            %s.LoadFromLines(lines);\n' % struct['name']
            if i + 1 == len(descriptors):
                content += '\n'
                content += '            if (completeFunc != null) completeFunc();\n'
            content += '        });\n\n'
        content += '    }\n'

        content += '}\n\n'
        return content

    def generate_class(self, struct):
        content = '\n'
        content += self.gen_cs_struct(struct)
        content += self.gen_static_data(struct)
        content += self.gen_parse_method(struct)
        content += self.gen_load_method(struct)
        content += self.gen_get_method(struct)
        content += self.gen_range_method(struct)
        content += '}\n\n'
        return content

    def run(self, descriptors, params):
        content = '// This file is auto-generated by taxi v%s, DO NOT EDIT!\n\n' % version.VER_STRING
        content += 'using System;\n'
        content += 'using System.IO;\n'
        content += 'using System.Collections.Generic;\n'

        if 'pkg' in params:
            content += '\nnamespace %s\n{\n' % params['pkg']

        for struct in descriptors:
            genutil.setup_comment(struct)
            genutil.setup_key_value_mode(struct)

        for struct in descriptors:
            content += self.generate_class(struct)

        content += self.gen_global_class(descriptors)

        if 'pkg' in params:
            content += '\n}\n'  # namespace

        filename = params.get(predef.OptionOutSourceFile, 'AutogenConfig.cs')
        filename = os.path.abspath(filename)
        strutil.compare_and_save_content(filename, content, 'utf-8')
        print('wrote source file to', filename)
