## LangChain VectorStore for InterSystems IRIS

`langchain_intersystems.IRISVectorStore` is an implementation of a LangChain VectorStore that stores vectorized documents in an InterSystems IRIS database. See the [LangChain VectorStore documentation](https://reference.langchain.com/python/langchain_core/vectorstores/) for general documentation for how to use this class. See the docstrings in the `IRISVectorStore` class for more details.

### Requirements

- InterSystems IRIS 2025.1+
- Python 3.10+

### Build and Install

Install the `build` package if it is not already installed.
```commandline
pip install build
```

Build the wheel.
```commandline
python -m build --wheel
```

Install the wheel.
```commandline
pip install dist/langchain_intersystems-0.0.1-py3-none-any.whl
```

### Example Usage

The following example assumes that
- Python package dependencies have been installed with `pip install -r requirements.txt`.
- Ollama is running locally with the `mxbai-embed-large` model installed.
- An InterSystems IRIS instance is listening at localhost:1972 with default username and password.

```Python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_intersystems import IRISVectorStore, SimilarityMetric, Predicate
from langchain_ollama import OllamaEmbeddings

documents = TextLoader("state_of_the_union.txt", encoding='utf-8').load()
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

vs = IRISVectorStore(
    OllamaEmbeddings(model='mxbai-embed-large'),
    connect_args=('localhost', 1972, 'USER', '_system', 'SYS'),
    collection_name='langchain',
    replace_collection=True,
    similarity_metric=SimilarityMetric.COSINE
)
vs.add_documents(docs)
for items in vs.similarity_search_with_score('Freedom to Vote Act', filter={'source': (Predicate.EQUAL, 'state_of_the_union.txt')}):
    print(repr(items))
```

### Testing

LangChain publishes a package [`langchain-tests`](https://pypi.org/project/langchain-tests/) which contains a standard set of tests for LangChain integrations and provides a way to extend them. The [`tests/integration_tests/test_vectorstore.py`](tests/integration_tests/test_vectorstore.py) file implements the standard `VectorStore` tests and adds additional ones. Assuming that Python package dependencies have been installed with `pip install -r requirements.txt`, simply run the command `pytest` at the root of the repository to run those tests. Edit [`tests/integration_tests/irisconfig.json`](tests/integration_tests/irisconfig.json) if your IRIS instance is listening at a non-default port or does not have the default username and password.

More tests can be added to [`tests/integration_tests/test_vectorstore.py`](tests/integration_tests/test_vectorstore.py) if desired.

### Metadata Limitations

The LangChain [Document](https://reference.langchain.com/python/langchain_core/documents/#langchain_core.documents.base.Document) object has a `metadata` field that supports an arbitrary `dict` of key-value pairs. `IRISVectorStore`, however, has stricter requirements and limitations regarding metadata format.

#### Keys
- Keys must have type `str`, contain only alphanumeric characters and underscores, and have a maximum length of `126`. An exception is raised if an invalid key is encountered.
- Keys are normalized to lowercase when stored. Consequently, one document cannot have two metadata keys that differ by case only. An exception is raised if such a document is encountered.

#### Value Types
- `None` values are ignored. For example, `{'key1': 1, 'key2': None}` is treated the same as `{'key1': 1}`. In both cases, a SQL `NULL` value is stored in the backend SQL column corresponding to `'key2'`.
- Supported value types are `str`, `bytes`, `int`, `float`, `bool`, `decimal.Decimal`, `datetime.date`, `datetime.time`, `datetime.datetime`, and `uuid.UUID`. An exception is raised if an unsupported value type is encountered.
- All non-`None` values for a given key must have the same type. For example, an exception is raised if an attempt is made to store a document with metadata `{'key': 1}` and another with metadata `{'key': '1'}`.

#### Value Limits
- `str` and `bytes` values have a maximum length of `1024`. Longer values result in an exception.
- `int` values must be in the range `-9223372036854775808` to `9223372036854775807`. Out-of-range values result in an exception.
- `decimal.Decimal` values must be in the range `decimal.Decimal('-999999999999999999')` to `decimal.Decimal('999999999999999999')`. `decimal.Decimal('NaN')`, `decimal.Decimal('-Infinity')`, and `decimal.Decimal('Infinity')` are invalid. Invalid or out-of-range values result in an exception.
- `decimal.Decimal` values with more than 9 digits after the decimal point are rounded to 9 post-decimal-point digits. Values with more than 18 total digits of precision are rounded to 18 digits. Rounded values result in a warning.

### Metadata Filtering

Similarity search functions have a `filter` parameter which allows filtering results based on metadata fields using a flexible and composable SQL-inspired syntax. Filters are expressed as nested Python `dict`s that describe logical and comparison operations using the `langchain_intersystems.Predicate` enumeration. Each key represents either:
- a (case-insensitive) **metadata field name** (e.g. `'author'`, `'year'`, `'category'`), or
- a **logical operator** (e.g. `Predicate.AND`, `Predicate.OR`, `Predicate.NOT`).

A value can be:
- a **predicate expression** &mdash; a tuple containing a predicate and its argument(s), e.g. `(Predicate.EQUAL, 'value')` or `(Predicate.IS_NULL,)`.
- a **nested filter** &mdash; additional `dict`(s) of field conditions combined with logical operators.
- a **literal value** &mdash; value used for equality comparison (shorthand for `(Predicate.EQUAL, 'value')`)

The basic structure of a filter is:

```
{ field_name: (predicate, value, [optional_arguments]) }
```

Logical combination:
- Use `Predicate.AND` or `Predicate.OR` as `dict` keys whose values are `list`s of filters.
- Use `Predicate.NOT` with a single filter (`dict`) to negate a condition.
- When a `dict` contains multiple keys, the conditions are implicitly ANDed together.

Predicates can be specified as `Predicate` enum values or their `str` equivalents. The following table summarizes all supported predicates.

| Predicate as `Predicate` enum | Predicate as `str` | IRIS SQL equivalent     |
|-------------------------------|--------------------|-------------------------|
| `AND`                         | `'$and'`           | `AND`                   |
| `OR`                          | `'$or'`            | `OR`                    |
| `NOT`                         | `'$not'`           | `NOT`                   |
| `EQUAL`                       | `'$eq'`            | `= ?`                   |
| `NOT_EQUAL`                   | `'$ne'`            | `!= ?`                  |
| `GREATER_THAN`                | `'$gt'`            | `> ?`                   |
| `GREATER_THAN_OR_EQUAL`       | `'$gte'`           | `>= ?`                  |
| `LESS_THAN`                   | `'$lt'`            | `< ?`                   |
| `LESS_THAN_OR_EQUAL`          | `'$lte'`           | `<= ?`                  |
| `IS_NULL`                     | `'$isnull'`        | `IS NULL`               |
| `IS_NOT_NULL`                 | `'$notnull'`       | `IS NOT NULL`           |
| `BETWEEN`                     | `'$between'`       | `BETWEEN ? AND ?`       |
| `IN`                          | `'$in'`            | `IN (?,?,[,...])`       |
| `CONTAINS`                    | `'$contains'`      | `[ ?`                   |
| `NOT_CONTAINS`                | `'$ncontains'`     | `NOT[ ?`                |
| `FOLLOWS`                     | `'$follows'`       | `] ?`                   |
| `NOT_FOLLOWS`                 | `'$nfollows'`      | `NOT] ?`                |
| `STARTS_WITH`                 | `'$startswith'`    | `%STARTSWITH ?`         |
| `LIKE`                        | `'$like'`          | `LIKE ? [ESCAPE ?]`     |
| `MATCHES`                     | `'$matches'`       | `%MATCHES ? [ESCAPE ?]` |
| `PATTERN`                     | `'$pattern'`       | `%PATTERN ?`            |

The following examples demonstrate how to use all the predicates.

```Python
# key1 metadata field equals 'value1'
{'key1': (Predicate.EQUAL, 'value1')}

# key1 equals 'value1'; uses equivalent string literal instead of Predicate
# enum
{'key1': ('$eq', 'value1')}

# key1 equals 'value1'; uses equivalent shorthand
{'key1': 'value1'}

# key1 equals 'value1' and key2 is greater than 0
{
    'key1': (Predicate.EQUAL, 'value1'),
    'key2': (Predicate.GREATER_THAN, 0)
}

# key1 is greater than or equal to 0 and is less than 5
{
    Predicate.AND: [
        {'key1': (Predicate.GREATER_THAN_OR_EQUAL, 0)},
        {'key1': (Predicate.LESS_THAN, 5)}
    ]
}

# key1 is not equal to 0 or key2 is less than or equal to 5
{
    Predicate.OR: [
        {'key1': (Predicate.NOT_EQUAL, 0)},
        {'key2': (Predicate.LESS_THAN_OR_EQUAL, 5)}
    ]
}

# key1 exists, key2 does not exist, and key3 and key4 do not both exist
{
    'key1': (Predicate.IS_NOT_NULL,),
    'key2': (Predicate.IS_NULL,),
    Predicate.NOT: {
        'key3': (Predicate.IS_NOT_NULL,),
        'key4': (Predicate.IS_NOT_NULL,)
    }
}

# key1 is between 0 and 5, inclusive
{'key1': (Predicate.BETWEEN, 0, 5)}

# key1 is 'value1', 'value2', or 'value3'
{'key1': (Predicate.IN, ['value1', 'value2', 'value3'])}

# key1 contains 'value1' as a substring and key2 does not
{
    'key1': (Predicate.CONTAINS, 'value1'),
    'key2': (Predicate.NOT_CONTAINS, 'value1')
}

# key1 is after 'value1' in collation sequence and key2 is not
{
    'key1': (Predicate.FOLLOWS, 'value1'),
    'key2': (Predicate.NOT_FOLLOWS, 'value1')
}

# key1 starts with 'value1'
{'key1': (Predicate.STARTS_WITH, 'value1')}

# key1 matches the pattern string 'value1' with literals and wildcards, and
# key2 matches the pattern string 'value2' with the backslash escape character.
{
    'key1': (Predicate.LIKE, 'value1'),
    'key2': (Predicate.LIKE, 'value2', '\\')
}

# key1 matches the pattern string 'value1' with literals, wildcards, and
# ranges; and key2 matches the pattern string 'value2' with the backslash
# escape character.
{
    'key1': (Predicate.MATCHES, 'value1'),
    'key2': (Predicate.MATCHES, 'value2', '\\')
}

# key1 matches the pattern string 'value1' with literals, wildcards, and
# character type codes.
{'key1': (Predicate.PATTERN, 'value1')}
```
