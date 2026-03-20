# Testing pydantic validation for User model
import pytest
import uuid

from app.util.cryptography import hash_password
from app.db_operations.user import (
    create_user,
    read_user,
    update_user,
    delete_user,
    UserNotFound,
)
from app.models.user import (
    BaseUser,
    User,
    UserCreate,
    UserPublic,
    UserPublicWithFollowers,
    UserUpdate,
    USER_ROLE,
)

from fastapi import Depends
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import create_engine, Session, select, SQLModel
from typing import Annotated


# Pydantic models validation tests
## BaseUser
def test_base_user_model_validation_successful_with_correct_fields():
    new_base_user = BaseUser(username="test", role=USER_ROLE.ADMIN)
    assert new_base_user.username == "test"
    assert new_base_user.role == USER_ROLE.ADMIN


def test_base_user_model_validation_fails_with_extra_fields():
    with pytest.raises(ValidationError):
        BaseUser(username="test", role=USER_ROLE.ADMIN, distniguished=True)  # type: ignore


def test_base_user_model_validation_fails_with_incorrect_fields():
    with pytest.raises(ValidationError):
        BaseUser(firstname="test", last_name="test", username="", hashed_password="", role=USER_ROLE.ADMIN)  # type: ignore


## UserCreate
def test_user_create_model_validation_successful_with_correct_fields():
    user_creation_data = UserCreate(
        username="test", password="test", role=USER_ROLE.ADMIN
    )
    assert user_creation_data.username == "test"
    assert user_creation_data.role == USER_ROLE.ADMIN
    assert user_creation_data.password == "test"


def test_user_create_model_validation_fails_with_missing_fields():
    with pytest.raises(ValidationError):
        UserCreate(username="test", role=USER_ROLE.ADMIN)  # type: ignore


def test_user_create_model_validation_fails_with_extra_fields():
    with pytest.raises(ValidationError):
        UserCreate(username="test", password="test", role=USER_ROLE.ADMIN, johhny=True)  # type: ignore


def test_user_create_model_validation_fails_with_incorrect_fields():
    with pytest.raises(ValidationError):
        UserCreate(firstname="test", secret="test", kind=USER_ROLE.ADMIN)  # type: ignore


## UserPublic
def test_user_public_model_validation_successful_with_correct_fields():
    generated_uuid = uuid.uuid4()
    user_public_data = UserPublic.model_validate(
        {"id": generated_uuid, "username": "test", "role": "ADMIN"}
    )
    assert user_public_data.id == generated_uuid
    assert user_public_data.username == "test"
    assert user_public_data.role == USER_ROLE.ADMIN


## UserPublicWithFollowers
def test_user_public_with_followers_model_validation_successful_with_correct_fields():
    generated_uuid_follower1 = uuid.uuid4()
    follower1 = UserPublic.model_validate(
        {"id": generated_uuid_follower1, "username": "inner1", "role": "ADMIN"}
    )

    generated_uuid_follower2 = uuid.uuid4()
    follower2 = UserPublic.model_validate(
        {"id": generated_uuid_follower2, "username": "inner2", "role": "ADMIN"}
    )

    generated_uuid = uuid.uuid4()
    user_public_data = UserPublicWithFollowers.model_validate(
        {
            "id": generated_uuid,
            "username": "test",
            "role": "ADMIN",
            "followers": [follower1, follower2],
            "following": [follower1],
        }
    )
    assert user_public_data.id == generated_uuid
    assert user_public_data.username == "test"
    assert user_public_data.role == USER_ROLE.ADMIN
    assert user_public_data.followers[0] == follower1  # type: ignore
    assert user_public_data.followers[1] == follower2  # type: ignore
    assert user_public_data.following[0] == follower1  # type: ignore


## UserUpdate
def test_user_update_model_validation_successful_with_correct_fields_all_fields():
    generated_uuid_follower1 = uuid.uuid4()

    generated_uuid_follower2 = uuid.uuid4()

    user_update_data = UserUpdate(
        username="test",
        password="test",
        role=USER_ROLE.ADMIN,
        followers_ids=[generated_uuid_follower1, generated_uuid_follower2],
    )
    assert user_update_data.username == "test"
    assert user_update_data.password == "test"
    assert user_update_data.role == USER_ROLE.ADMIN
    assert user_update_data.followers_ids[0] == generated_uuid_follower1  # type: ignore
    assert user_update_data.followers_ids[1] == generated_uuid_follower2  # type: ignore


def test_user_update_model_validation_successful_with_correct_fields_partial_fields():
    user_update_data = UserUpdate(password="test")
    assert user_update_data.password == "test"


def test_user_update_model_validation_fails_with_extra_fields():
    with pytest.raises(ValidationError):
        UserUpdate(username="test", password="test", role=USER_ROLE.ADMIN, johhny=True)  # type: ignore


def test_user_update_model_validation_fails_with_incorrect_fields():
    with pytest.raises(ValidationError):
        UserUpdate(firstname="test", secret="test", kind=USER_ROLE.ADMIN)  # type: ignore


## User Only a non-failure limited test due: #https://github.com/fastapi/sqlmodel/issues/453 Why does a SQLModel class with table=True not validate data ?
def test_user_model_validation_successful_with_correct_fields():
    new_user = User(username="test", hashed_password="test", role=USER_ROLE.ADMIN)
    assert new_user.username == "test"
    assert new_user.hashed_password == "test"
    assert new_user.role == USER_ROLE.ADMIN


# Database operations tests

engine_url = "sqlite:///"
engine = create_engine(engine_url)
SQLModel.metadata.create_all(engine)

existing_user_id = None


## User - Create
def test_create_user_creates_user_with_correct_fields():
    with Session(engine) as session:
        create_user(
            session, UserCreate(username="test", password="test", role=USER_ROLE.ADMIN)  # type: ignore
        )
        new_user_from_db = session.exec(
            select(User).where(User.username == "test")
        ).one()
        assert new_user_from_db.role == USER_ROLE.ADMIN
        global existing_user_id
        existing_user_id = new_user_from_db.id


def test_create_user_fails_with_non_unique_username():
    with pytest.raises(IntegrityError):
        with Session(engine) as session:
            create_user(
                session,
                UserCreate(username="test", password="test", role=USER_ROLE.ADMIN),
            )


def test_create_user_hashes_password_correctly():
    password = "test3"
    expected_hashed_password = hash_password(password)
    with Session(engine) as session:
        create_user(
            session,
            UserCreate(username="test3", password=password, role=USER_ROLE.ADMIN),
        )
        new_user_from_db = session.exec(
            select(User).where(User.username == "test3")
        ).one()
        assert new_user_from_db.hashed_password == expected_hashed_password


## User - Read
def test_read_user_by_username_returns_existing_user():
    with Session(engine) as session:
        existing_user = read_user(session, username="test3")
        assert not existing_user == None


def test_read_user_by_id_returns_existing_user():
    with Session(engine) as session:
        existing_user = read_user(session, id=existing_user_id)
        assert not existing_user == None


def test_read_user_by_username_raises_UserNotFound_when_user_not_found():
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            read_user(session, username="not_present")
        assert "User not_present not found." in str(exc.value)


def test_read_user_raises_ValueError_Exception_when_both_username_and_id_provided():
    with pytest.raises(ValueError):
        with Session(engine) as session:
            read_user(session, username="abc", id="abc")  # type: ignore


def test_read_user_raises_ValueError_Exception_when_no_username_or_id_provided():
    with pytest.raises(ValueError):
        with Session(engine) as session:
            read_user(session)


# User - Update
def test_update_user_correctly_executes_partial_update_on_existing_user():
    global existing_user_id
    with Session(engine) as session:
        updated_user = update_user(
            session, data=UserUpdate(username="updated_test"), id=existing_user_id
        )
        assert updated_user.username == "updated_test"
        assert updated_user.role == USER_ROLE.ADMIN  # Should remain unchaged


def test_update_user_raises_UserNotFound_Exception_when_user_does_not_exsist_for_username_provided():
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            update_user(
                session, data=UserUpdate(username="doesntexist"), username="nosuchuser"
            )
        assert str(exc.value) == "User nosuchuser not found."


def test_update_user_raises_UserNotFound_Exception_when_user_does_not_exsist_for_id_provided():
    non_existent_id = uuid.uuid4()
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            update_user(
                session, data=UserUpdate(username="doesntexist"), id=non_existent_id
            )
        assert str(exc.value) == f"User with id {non_existent_id} not found."


def test_update_user_correctly_updates_password_with_hashing():
    global existing_user_id
    new_password = "updated_password"
    new_password_hashed = hash_password(new_password)
    with Session(engine) as session:
        updated_user = update_user(
            session, data=UserUpdate(password=new_password), id=existing_user_id
        )
        assert updated_user.hashed_password == new_password_hashed


def test_update_user_correctly_executes_complete_update_on_existing_user():
    global existing_user_id
    new_password = "again_updated_password"
    new_password_hashed = hash_password(new_password)

    with Session(engine) as session:
        existing_user = read_user(session, username="test3")
        assert existing_user != None
        updated_user = update_user(
            session,
            data=UserUpdate(
                username="again_updated_test",
                password=new_password,
                role=USER_ROLE.REGULAR_USER,
                followers_ids=[existing_user.id],
            ),
            id=existing_user_id,
        )
        assert updated_user.username == "again_updated_test"
        assert updated_user.hashed_password == new_password_hashed
        assert updated_user.role == USER_ROLE.REGULAR_USER
        assert updated_user.followers[0] == existing_user


def test_update_user_raises_UserNotFound_Exception_when_all_followers_ids_not_found():
    random_non_existant_id = uuid.uuid4()
    with Session(engine) as session:
        with pytest.raises(UserNotFound):
            update_user(
                session,
                data=UserUpdate(followers_ids=[random_non_existant_id]),
                username="again_updated_test",
            )


def test_update_user_raises_UserNotFound_Exception_when_one_follower_id_not_found():
    global existing_user_id
    random_non_existant_id = uuid.uuid4()
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            update_user(
                session,
                data=UserUpdate(
                    followers_ids=[random_non_existant_id, existing_user_id]
                ),
                username="test3",
            )
        assert str(exc.value) == f"Followers: {random_non_existant_id} not found."


def test_update_user_permamanently_updates_the_follower():
    with Session(engine) as session:
        create_user(
            session,
            user=UserCreate(username="bbb", password="bbb", role=USER_ROLE.ADMIN),
        )

    follower_from_db_id = None
    with Session(engine) as session:
        follower_from_db = read_user(session, username="bbb")
        if follower_from_db:
            follower_from_db_id = follower_from_db.id
            update_user(
                session,
                data=UserUpdate(followers_ids=[follower_from_db.id]),
                username="test3",
            )

    with Session(engine) as session:
        user_from_db = read_user(session, username="test3")
        assert user_from_db != None
        assert user_from_db.followers[0].id == follower_from_db_id
        assert user_from_db.followers[0].username == "bbb"


def test_update_user_raises_ValueError_when_user_attempting_to_follow_himself():
    global existing_user_id
    with Session(engine) as session:
        with pytest.raises(ValueError):
            update_user(
                session,
                data=UserUpdate(followers_ids=[existing_user_id]),
                id=existing_user_id,
            )


## User - Delete
def test_user_delete_succesfully_deletes_existing_user():
    with Session(engine) as session:
        user_for_deletion = create_user(
            session,
            UserCreate(username="delete", password="delete", role=USER_ROLE.ADMIN),
        )

    with Session(engine) as session:
        delete_user(session, id=user_for_deletion.id)

    with Session(engine) as session:
        with pytest.raises(UserNotFound):
            assert read_user(session, id=user_for_deletion.id)


def test_user_delete_raises_UserNotFound_when_user_does_not_exist_when_username_provided():
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            delete_user(session, username="its_a_fiction")
        assert str(exc.value) == "User its_a_fiction not found."


def test_user_delete_raises_UserNotFound_when_user_does_not_exist():
    random_non_existent_id = uuid.uuid4()
    with Session(engine) as session:
        with pytest.raises(UserNotFound) as exc:
            delete_user(session, id=random_non_existent_id)
        assert str(exc.value) == f"User with id {random_non_existent_id} not found."


def test_user_delete_raises_ValueError_when_no_username_or_id_provided():
    with Session(engine) as session:
        with pytest.raises(ValueError):
            delete_user(session)
