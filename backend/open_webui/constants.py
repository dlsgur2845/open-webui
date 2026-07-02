from __future__ import annotations

import errno
from enum import Enum


_ERRNO_MESSAGES = {
    # File name is too long.
    errno.ENAMETOOLONG: '파일 이름이 너무 깁니다.',
    # The server is out of storage space.
    errno.ENOSPC: '서버 저장 공간이 부족합니다.',
    # Server storage quota exceeded.
    errno.EDQUOT: '서버 저장 공간 할당량을 초과했습니다.',
    # Server storage is not writable.
    errno.EACCES: '서버 저장소에 쓸 수 없습니다.',
    # Server storage is not writable.
    errno.EPERM: '서버 저장소에 쓸 수 없습니다.',
    # Server storage is not writable.
    errno.EROFS: '서버 저장소에 쓸 수 없습니다.',
}


def _error_message(err='', fallback='') -> str:
    # Something went wrong :/ / [ERROR: {err}]
    if not err:
        return '문제가 발생했습니다 :/'
    if isinstance(err, OSError) and err.errno in _ERRNO_MESSAGES:
        return f'[오류: {_ERRNO_MESSAGES[err.errno]}]'
    if isinstance(err, Exception):
        return f'[오류: {fallback}]' if fallback else '문제가 발생했습니다 :/'
    return f'[오류: {err}]'


class MESSAGES(str, Enum):
    DEFAULT = lambda msg='': f'{msg if msg else ""}'
    # The model '{model}' has been added successfully.
    MODEL_ADDED = lambda model='': f"모델 '{model}'이(가) 성공적으로 추가되었습니다."
    # The model '{model}' has been deleted successfully.
    MODEL_DELETED = lambda model='': f"모델 '{model}'이(가) 성공적으로 삭제되었습니다."


class WEBHOOK_MESSAGES(str, Enum):
    DEFAULT = lambda msg='': f'{msg if msg else ""}'
    # New user signed up: {username}
    USER_SIGNUP = lambda username='': (f'새 사용자 가입: {username}' if username else '새 사용자가 가입했습니다')


class ERROR_MESSAGES(str, Enum):
    def __str__(self) -> str:
        return super().__str__()

    DEFAULT = _error_message
    # Required environment variable not found. Terminating now.
    ENV_VAR_NOT_FOUND = '필수 환경 변수를 찾을 수 없습니다. 서버를 종료합니다.'
    # Oops! Something went wrong while creating your account. Please try again later. If the issue persists, contact support for assistance.
    CREATE_USER_ERROR = '계정 생성 중 문제가 발생했습니다. 나중에 다시 시도해주세요. 문제가 지속되면 관리자에게 문의하세요.'
    # Oops! Something went wrong. We encountered an issue while trying to delete the user. Please give it another shot.
    DELETE_USER_ERROR = '사용자 삭제 중 문제가 발생했습니다. 다시 시도해주세요.'
    # Uh-oh! This email does not match the email your provider is registered with. Please check your email and try again.
    EMAIL_MISMATCH = '이메일이 등록된 계정의 이메일과 일치하지 않습니다. 이메일을 확인하고 다시 시도해주세요.'
    # Uh-oh! This email is already registered. Sign in with your existing account or choose another email to start anew.
    EMAIL_TAKEN = '이미 등록된 이메일입니다. 기존 계정으로 로그인하거나 다른 이메일을 사용해주세요.'
    # Uh-oh! This username is already registered. Please choose another username.
    USERNAME_TAKEN = '이미 등록된 사용자명입니다. 다른 사용자명을 선택해주세요.'
    # Uh-oh! The password you entered is too long. Please make sure your password is less than 72 bytes long.
    PASSWORD_TOO_LONG = '비밀번호가 너무 깁니다. 72바이트 미만으로 설정해주세요.'
    # Uh-oh! This command is already registered. Please choose another command string.
    COMMAND_TAKEN = '이미 등록된 명령어입니다. 다른 명령어를 선택해주세요.'
    # Uh-oh! This file is already registered. Please choose another file.
    FILE_EXISTS = '이미 등록된 파일입니다. 다른 파일을 선택해주세요.'

    # Uh-oh! This id is already registered. Please choose another id string.
    ID_TAKEN = '이미 등록된 ID입니다. 다른 ID를 선택해주세요.'
    # Uh-oh! This model id is already registered. Please choose another model id string.
    MODEL_ID_TAKEN = '이미 등록된 모델 ID입니다. 다른 모델 ID를 선택해주세요.'
    # Uh-oh! This name tag is already registered. Please choose another name tag string.
    NAME_TAG_TAKEN = '이미 등록된 이름 태그입니다. 다른 이름 태그를 선택해주세요.'
    # The model id is too long. Please make sure your model id is less than 256 characters long.
    MODEL_ID_TOO_LONG = '모델 ID가 너무 깁니다. 256자 미만으로 설정해주세요.'

    # Your session has expired or the token is invalid. Please sign in again.
    INVALID_TOKEN = '세션이 만료되었거나 토큰이 유효하지 않습니다. 다시 로그인해주세요.'
    # The email or password provided is incorrect. Please check for typos and try logging in again.
    INVALID_CRED = '이메일 또는 비밀번호가 올바르지 않습니다. 확인 후 다시 시도해주세요.'
    # The email format you entered is invalid. Please double-check and make sure you're using a valid email address (e.g., yourname@example.com).
    INVALID_EMAIL_FORMAT = '이메일 형식이 올바르지 않습니다. 올바른 이메일 주소를 입력해주세요 (예: yourname@example.com).'
    # The password provided is incorrect. Please check for typos and try again.
    INCORRECT_PASSWORD = '비밀번호가 올바르지 않습니다. 확인 후 다시 시도해주세요.'
    # Your provider has not provided a trusted header. Please contact your administrator for assistance.
    INVALID_TRUSTED_HEADER = '인증 헤더가 제공되지 않았습니다. 관리자에게 문의하세요.'

    # You can't turn off authentication because there are existing users. If you want to disable WEBUI_AUTH, make sure your web interface doesn't have any existing users and is a fresh installation.
    EXISTING_USERS = '기존 사용자가 있어 인증을 비활성화할 수 없습니다. WEBUI_AUTH를 비활성화하려면 기존 사용자가 없는 새 설치 상태여야 합니다.'

    # 401 Unauthorized
    UNAUTHORIZED = '401 인증되지 않음'
    # You do not have permission to access this resource. Please contact your administrator for assistance.
    ACCESS_PROHIBITED = '이 리소스에 접근할 권한이 없습니다. 관리자에게 문의하세요.'
    # The requested action has been restricted as a security measure.
    ACTION_PROHIBITED = '보안상의 이유로 해당 작업이 제한되었습니다.'

    # FILE_NOT_SENT
    FILE_NOT_SENT = '파일이 전송되지 않았습니다.'
    # Oops! It seems like the file format you're trying to upload is not supported. Please upload a file with a supported format and try again.
    FILE_NOT_SUPPORTED = '지원하지 않는 파일 형식입니다.'

    # We could not find what you're looking for :/
    NOT_FOUND = '요청하신 항목을 찾을 수 없습니다.'
    # We could not find what you're looking for :/
    USER_NOT_FOUND = '사용자를 찾을 수 없습니다.'
    # Oops! It looks like there's a hiccup. The API key is missing. Please make sure to provide a valid API key to access this feature.
    API_KEY_NOT_FOUND = 'API 키가 누락되었습니다. 유효한 API 키를 제공해주세요.'
    # Use of API key is not enabled in the environment.
    API_KEY_NOT_ALLOWED = '이 환경에서는 API 키 사용이 허용되지 않습니다.'

    # Unusual activities detected, please try again in a few minutes.
    MALICIOUS = '비정상적인 활동이 감지되었습니다. 잠시 후 다시 시도해주세요.'

    # Pandoc is not installed on the server. Please contact your administrator for assistance.
    PANDOC_NOT_INSTALLED = '서버에 Pandoc이 설치되어 있지 않습니다. 관리자에게 문의하세요.'
    # Invalid format. Please use the correct format{err}
    INCORRECT_FORMAT = lambda err='': f'형식이 올바르지 않습니다. 올바른 형식을 사용해주세요{err}'
    # API rate limit exceeded
    RATE_LIMIT_EXCEEDED = 'API 요청 한도를 초과했습니다.'

    # Model '{name}' was not found
    MODEL_NOT_FOUND = lambda name='': f"모델 '{name}'을(를) 찾을 수 없습니다."
    # OpenAI API was not found
    OPENAI_NOT_FOUND = lambda name='': 'OpenAI API를 찾을 수 없습니다.'
    # WebUI could not connect to Ollama
    OLLAMA_NOT_FOUND = 'Ollama에 연결할 수 없습니다.'
    # Oops! Something went wrong while creating your API key. Please try again later. If the issue persists, contact support for assistance.
    CREATE_API_KEY_ERROR = 'API 키 생성 중 문제가 발생했습니다. 나중에 다시 시도해주세요. 문제가 지속되면 관리자에게 문의하세요.'
    # API key creation is not allowed in the environment.
    API_KEY_CREATION_NOT_ALLOWED = '이 환경에서는 API 키 생성이 허용되지 않습니다.'

    # The content provided is empty. Please ensure that there is text or data present before proceeding.
    EMPTY_CONTENT = '내용이 비어있습니다. 텍스트나 데이터를 입력해주세요.'

    # This feature is only available with SQLite databases.
    DB_NOT_SQLITE = '이 기능은 SQLite 데이터베이스에서만 사용 가능합니다.'

    # The URL you provided is invalid. Please double-check and try again.
    INVALID_URL = 'URL이 올바르지 않습니다. 확인 후 다시 시도해주세요.'

    # Something went wrong while searching the web.
    WEB_SEARCH_ERROR = lambda err='': err if err else '웹 검색 중 문제가 발생했습니다.'

    # The Ollama API is disabled. Please enable it to use this feature.
    OLLAMA_API_DISABLED = 'Ollama API가 비활성화되어 있습니다. 이 기능을 사용하려면 활성화해주세요.'

    # Oops! The file you're trying to upload is too large. Please upload a file that is less than {size}.
    FILE_TOO_LARGE = lambda size='': f'파일이 너무 큽니다. {size} 미만의 파일을 업로드해주세요.'

    # Duplicate content detected. Please provide unique content to proceed.
    DUPLICATE_CONTENT = '중복된 내용이 감지되었습니다. 고유한 내용을 제공해주세요.'
    # Extracted content is not available for this file. Please ensure that the file is processed before proceeding.
    FILE_NOT_PROCESSED = '이 파일에서 추출된 내용을 사용할 수 없습니다. 파일이 처리되었는지 확인해주세요.'

    # The password does not meet the required validation criteria.
    INVALID_PASSWORD = lambda err='': err if err else '비밀번호가 요구 조건을 충족하지 않습니다.'

    # Password validation errors
    PASSWORD_TOO_SHORT = '비밀번호는 최소 8자 이상이어야 합니다.'
    PASSWORD_MISSING_CHARS = '비밀번호는 영문자, 숫자, 특수문자를 각각 1개 이상 포함해야 합니다.'
    PASSWORD_SEQUENTIAL = '비밀번호에 4자 이상의 연속된 문자나 숫자를 사용할 수 없습니다 (예: 1234, abcd).'
    PASSWORD_REPETITIVE = '비밀번호에 4자 이상의 반복된 문자나 숫자를 사용할 수 없습니다 (예: 1111, aaaa).'
    PASSWORD_CONTAINS_ACCOUNT_INFO = '비밀번호에 이메일 아이디나 이름을 포함할 수 없습니다.'
    PASSWORD_COMMON = '비밀번호로 사용할 수 없는 쉬운 문자열이 포함되어 있습니다.'

    # Automation limit reached ({size})
    AUTOMATION_LIMIT_EXCEEDED = lambda size='': f'자동화 개수 한도에 도달했습니다 ({size})'
    # Schedule too frequent. Minimum interval is {interval} seconds.
    AUTOMATION_TOO_FREQUENT = lambda interval='': f'일정 주기가 너무 짧습니다. 최소 간격은 {interval}초입니다.'
    # Invalid RRULE: {err}
    AUTOMATION_INVALID_RRULE = lambda err='': f'유효하지 않은 RRULE: {err}'
    # RRULE has no future occurrences
    AUTOMATION_NO_FUTURE_RUNS = 'RRULE에 향후 실행 일정이 없습니다.'

    # {name} is disabled
    FEATURE_DISABLED = lambda name='': f'{name} 기능이 비활성화되어 있습니다.'
    # Input prompt exceeds maximum length of {size}
    INPUT_TOO_LONG = lambda size='': f'입력 프롬프트가 최대 길이 {size}을(를) 초과했습니다.'
    # Open WebUI: Server Connection Error
    SERVER_CONNECTION_ERROR = '서버 연결 오류가 발생했습니다. 관리자에게 문의하세요.'
    # Required field {name} is empty
    REQUIRED_FIELD_EMPTY = lambda name='': f'필수 항목 {name}이(가) 비어 있습니다.'
    # Provider '{name}' is not configured
    OAUTH_NOT_CONFIGURED = lambda name='': f"'{name}' 제공자가 구성되어 있지 않습니다."


class TASKS(str, Enum):
    def __str__(self) -> str:
        return super().__str__()

    DEFAULT = lambda task='': f'{task if task else "generation"}'
    TITLE_GENERATION = 'title_generation'
    FOLLOW_UP_GENERATION = 'follow_up_generation'
    TAGS_GENERATION = 'tags_generation'
    EMOJI_GENERATION = 'emoji_generation'
    QUERY_GENERATION = 'query_generation'
    IMAGE_PROMPT_GENERATION = 'image_prompt_generation'
    AUTOCOMPLETE_GENERATION = 'autocomplete_generation'
    FUNCTION_CALLING = 'function_calling'
    MOA_RESPONSE_GENERATION = 'moa_response_generation'
