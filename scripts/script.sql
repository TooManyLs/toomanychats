BEGIN;

CREATE TABLE IF NOT EXISTS public.users
(
    id bigserial NOT NULL,
    name text COLLATE pg_catalog."default" NOT NULL,
    password bytea NOT NULL,
    salt bytea NOT NULL,
    totp_secret text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT "users_pkey" PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS public.userkeys
(
    device_id bytea NOT NULL,
    user_id bigint NOT NULL,
    public_key text COLLATE pg_catalog."default" NOT NULL,
    last_rotation timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "userkeys_pkey" PRIMARY KEY (device_id),
    CONSTRAINT "userkeys_user_id_fkey" FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

COMMIT;
