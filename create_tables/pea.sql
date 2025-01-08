-- Table: public.pea

-- DROP TABLE IF EXISTS public.pea;

CREATE TABLE IF NOT EXISTS public.pea
(
    date date NOT NULL,
    compte bigint NOT NULL,
    solde real NOT NULL,
    type_compte character(30) COLLATE pg_catalog."default",
    CONSTRAINT unicity UNIQUE (date, compte)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.pea
    OWNER to finance;