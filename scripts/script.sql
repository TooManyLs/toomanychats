BEGIN;

CREATE TABLE IF NOT EXISTS public.users
(
    id bigserial PRIMARY KEY,
    name varchar(50) NOT NULL,
    password bytea NOT NULL,
    salt bytea NOT NULL,
    totp_secret varchar(32) NOT NULL
);
CREATE INDEX ON public.users (name);

CREATE TABLE IF NOT EXISTS public.userkeys
(
    device_id bytea PRIMARY KEY,
    user_id bigint NOT NULL,
    public_key text COLLATE pg_catalog."default" NOT NULL,
    last_rotation timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS public.chatrooms
(
    id uuid PRIMARY KEY,
    title varchar(250),
    image path,
    admin bigint NOT NULL,
    FOREIGN KEY (admin) REFERENCES public.users (id) MATCH SIMPLE
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

CREATE TABLE IF NOT EXISTS public.chatroom_members
(
    id bigserial PRIMARY KEY,
    user_id bigint NOT NULL,
    chatroom_id uuid NOT NULL,
    FOREIGN KEY (user_id) REFERENCES public.users (id) MATCH SIMPLE
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms (id) MATCH SIMPLE
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
CREATE INDEX ON public.chatroom_members (chatroom_id);

CREATE TABLE IF NOT EXISTS public.messages
(
    id bigserial NOT NULL,
    chatroom_id uuid NOT NULL,
    sender_id bigint NOT NULL,
    message_type varchar(3) NOT NULL,
    length bigint NOT NULL,
    content path NOT NULL,
    basename varchar(250),
    preview path,
    timestamp timestamp with time zone NOT NULL,
    PRIMARY KEY (id, timestamp),
    FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms (id) MATCH SIMPLE
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES public.users (id) MATCH SIMPLE
        ON DELETE CASCADE
        ON UPDATE CASCADE
)
PARTITION BY RANGE (timestamp);
CREATE INDEX ON public.messages (chatroom_id);

-- Function for managing partition creation and deletion on messages table
CREATE OR REPLACE FUNCTION manage_messages_partitions()
RETURNS VOID AS $$
DECLARE
    current_week_start DATE;
    previous_to_last_week_start DATE;
    partition_name TEXT;
BEGIN
    current_week_start := DATE_TRUNC('week', CURRENT_TIMESTAMP);
    previous_to_last_week_start := current_week_start - INTERVAL '2 week';

    -- Create new partition for current week
    partition_name := 'messages_' || TO_CHAR(current_week_start, 'YYYY_MM_DD');
    EXECUTE format('CREATE TABLE IF NOT EXISTS public.%s PARTITION OF public.messages
                    FOR VALUES FROM (''%s'') TO (''%s'')',
                    partition_name,
                    current_week_start,
                    current_week_start + INTERVAL '1 week');

    -- Delete two weeks old partition
    partition_name := 'messages_' || TO_CHAR(previous_to_last_week_start, 'YYYY_MM_DD');
    EXECUTE format('DROP TABLE IF EXISTS public.%s',
                    partition_name);
END;
$$ LANGUAGE plpgsql;

-- Create first partition
SELECT manage_messages_partitions();

COMMIT;
