-- Table: public.epargne

-- DROP TABLE IF EXISTS public.epargne;

CREATE TABLE IF NOT EXISTS public.epargne
(
    date date NOT NULL,
    compte bigint NOT NULL,
    solde real NOT NULL,
    type_compte character(15) COLLATE pg_catalog."default",
    CONSTRAINT unicity UNIQUE (date, compte)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.epargne
    OWNER to finance;