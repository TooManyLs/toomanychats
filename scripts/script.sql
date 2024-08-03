BEGIN;

CREATE TABLE IF NOT EXISTS public."UserKeys"
(
    device_id bytea NOT NULL,
    user_id integer NOT NULL,
    public_key text COLLATE pg_catalog."default" NOT NULL,
    last_rotation timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "UserKeys_pkey" PRIMARY KEY (device_id)
);

CREATE TABLE IF NOT EXISTS public."Users"
(
    user_id serial NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    password bytea NOT NULL,
    salt bytea NOT NULL,
    totp_secret text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "Users_pkey" PRIMARY KEY (user_id)
);

ALTER TABLE IF EXISTS public."UserKeys"
    ADD CONSTRAINT "UserKeys_user_id_fkey" FOREIGN KEY (user_id)
    REFERENCES public."Users" (user_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE
    NOT VALID;

END;