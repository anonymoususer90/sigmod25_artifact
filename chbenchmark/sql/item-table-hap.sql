--
-- Name: item; Type: TABLE; Schema: public; 
--
CREATE TABLE ITEM (
    I_ID INTEGER NOT NULL, 
    I_IM_ID INTEGER NOT NULL, 
    I_NAME CHARACTER VARYING(24) NOT NULL,
    I_PRICE NUMERIC(5,2) NOT NULL, 
    I_DATA CHARACTER VARYING(50) NOT NULL,
    CONSTRAINT ITEM_I1 PRIMARY KEY (I_ID)) USING HAP;
