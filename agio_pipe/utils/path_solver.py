"""
Tokens:
<name> - reference to the other template
{name} - variable
({name}) - optional variable
(v{version:04d}) - optional variable with optional text and formatting
{current_date:%Y-%m-%d} - date formatting
{mydict['key']}, {mydict.key} - access to dict key or object attribute
{my_obj[key]} - access to object attribute using attribute name from context
{project.name:lower:strip} - apply formatting functions to variable value

Example:
"<roots.main>/{project.name}/{entity.name}/({entity.variant})/publish/v{version:04d}"
"""
import re
from datetime import datetime
from agio.core.utils import extract_variable


class PathTokenizerError(Exception):
    pass


class VariableNotFoundError(PathTokenizerError):
    pass


class EmptyValueError(PathTokenizerError):
    pass


class IncorrectTemplateError(PathTokenizerError):
    pass


_format_functions = {
    'title': str.title,
    'upper': str.upper,
    'lower': str.lower,
    'strip': str.strip,
    'rstrip': str.rstrip,
    'lstrip': str.lstrip,
}


class TokenBase:
    name = None
    pattern = None
    def __init__(self, value):
        self.value = value

    @classmethod
    def match(cls, value: str):
        match = cls.pattern.search(value)
        if match:
            return cls(match.group(0))

    def __str__(self):
        return repr(self.value)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.value!r}>'

    def solve(self, context: dict) -> str:
        raise NotImplementedError

    def solve_variable(self, variable_name: str, context: dict, attributes: str = None, formats: str = None) -> str:
        names_chain = variable_name.split('.')
        if attributes:
            attributes = attributes.strip('[]')
            if re.match(r"^([\"'].*?[\"'])$", attributes):
                names_chain.append(attributes.strip('\'"'))
            elif re.match(r"^[\w._]+$", attributes):
                attr_name = self.solve_variable(attributes, context)
                names_chain.append(attr_name)
            else:
                raise IncorrectTemplateError
        raw_value = self.extract_value(names_chain, context)
        if not raw_value:
            raise EmptyValueError(f'Variable {variable_name!r} is empty')
        formatted_value = self.apply_formatting(raw_value, formats, context)
        return formatted_value

    def extract_value(self, names: list[str], context: dict) -> str:
        """
        Extract value fom context
        """
        try:
            value = extract_variable.get_nested_value(names, context)
        except (KeyError, AttributeError, IndexError) as e:
            raise VariableNotFoundError from e
        return value

    def apply_formatting(self, value, formats: list|str, context: dict) -> str:
        if not formats:
            return value
        if isinstance(formats, str):
            formats = formats.split(':')
        for frmt in formats:
            if frmt in _format_functions:
                value = _format_functions[frmt](str(value))
            else:
                value = f"{value:{frmt}}"
        return value


class TokenRegular(TokenBase):
    pattern = re.compile(
        r"\{"       # opening parenthesis
        r"[^}]+"    # any variable
        r"}",       # closing parenthesis
        re.VERBOSE)

    def extract_parts(self, value: str):
        parts = re.search(
            r"\{"
            r"(?P<name>[\w\d._]+)"  # variable name
            r"(?P<attr>\[[\w._'\"]+])?" # variable attribute name
            r":?(?P<formats>.*?)?"  # formatting
            r"}",
            value, re.VERBOSE)
        if not parts:
            raise IncorrectTemplateError
        return parts.groupdict()

    def solve(self, context: dict):
        parts = self.extract_parts(self.value)
        return self.solve_variable(
            parts["name"], context, parts['attr'], parts["formats"])


class TokenOptional(TokenRegular):
    pattern = re.compile(
        r"\(!?[^(){}]*" # opening optional parenthesis 
        r"\{[^}]+}"     # variable
        r"[^(){}]*\)",  # closing optional parenthesis
        re.VERBOSE
    )

    def solve(self, context: dict):
        match = re.match(
            r"\("                   # opening optional parenthesis 
            r"(?P<strong>!?)"       # strong or not: mark "!"
            r"(?P<before>.*?)"      # text before variable
            r"(?P<value>\{.*?})"    # variable
            r"(?P<after>.*?)"       # text after variable
            r"\)",                  # closing optional parenthesis
            self.value, re.VERBOSE)
        if not match:
            raise IncorrectTemplateError
        parts = match.groupdict()
        skip_empty_values = not parts.get('strong').strip()
        self.value = parts['value']
        try:
            result = super().solve(context)
        except VariableNotFoundError:
            return ''
        except EmptyValueError:
            if skip_empty_values:
                return ''
            raise
        return f'{parts["before"]}{result}{parts["after"]}'


class TokenExternal(TokenBase):
    pattern = re.compile(
        r"<"        # opening external parenthesis 
        r"[^<>]+"   # external template name
        r">",       # closing optional parenthesis
        re.VERBOSE
    )

    def solve(self, context: dict):
        match = re.match(r"<([\w_]+)>", self.value)
        if match:
            return match.group(1)
        raise IncorrectTemplateError


class TemplateSolver:
    token_specs = {
        "external": TokenExternal,
        "optional": TokenOptional,
        "regular": TokenRegular,
    }

    def __init__(self, template_list: dict):
        self.templates = template_list

    def solve(self, template_name: str, context: dict, **kwargs) -> str:
        # get template
        template = self.templates.get(template_name)
        if not template:
            raise KeyError(f"Template '{template_name}' not found: {self.templates.keys()}")
        # tokenize template
        tokens, tmpl = self.tokenize_string(template)
        for holder, token in tokens.items():
            token: TokenBase
            if isinstance(token, TokenExternal):
                template_name = token.solve(context)
                value = self.solve(template_name, context)
            else:
                value = token.solve(context)
            tmpl = tmpl.replace(holder, str(value))
        # fix slashes
        if not kwargs.get('no_fix_slashes'): # disable removing multiple slashes
            tmpl = re.sub(r"\\\\+", r"\\", re.sub(r"//+", r"/", tmpl))
        return tmpl

    def tokenize_string(self, raw_template: str) -> (dict, str):
        raw_tokens = {}
        index = 0
        it = 0
        while True:
            it += 1
            if it > 100:
                break
            for name, tkn in self.token_specs.items():
                token = tkn.match(raw_template)
                if token:
                    placeholder = "#%s#" % index
                    raw_template = raw_template.replace(token.value, placeholder, 1)
                    raw_tokens[placeholder] = token
                    index += 1
                    break
            else:
                break
        return raw_tokens, raw_template


if __name__ == '__main__':
    templates = {
    'root_path': '{root.projects}',
    'project_root': '<root_path>/{project.name:lower:strip}/',
    'publish': '<project_root>/{entity.name:lower}/(!{entity.mod})/{task.name}/publish//{current_date:%Y-%m-%d}/v{version:04d}',
    'full': "<project_root>/shots/{current_date:%Y-%m-%d}/{entity['name']}/"
            "(_{entity.variant}_)/step/{steps[step_name]}/publish/{version:04d}"
    }

    ctx = {
        'project': {'name': "TEST "},
        'root': {"projects": '/mnt/projects'},
        'entity': {'name': "Asset1", 'mod': 'mod1'},
        'task': {'name': "modeling"},
        'version': 25,
        'current_date': datetime.now(),
        "step_name": 'model',
        'steps': {'model': 'MODELING', 'txd': 'TEXTURING'}
    }
    ts = TemplateSolver(templates)
    print(ts.solve('publish', ctx))
    print(ts.solve('full', ctx))
