import os
import subprocess
import rdflib
from rdflib import URIRef

from .RML import *
from .SHACL import *


class EnrichSHACL:
    def __init__(self):
        self.RML = RML()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.XSDNS = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')

        self.enrich_stats = {}

    def enrich(self, g, s, p, o):
        # return if the subject-predicate pair is already present to avoid conflicts in constraints
        # unless it's a name, description or label
        if (
            p
            not in [
                URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                self.shaclNS.description,
                self.shaclNS.name,
            ]
            and (s, p, None) in g
        ):
            return

        # get the datatype of the corresponding subject
        # only allow in/exclusiveness in value-type-datatypes and length on string-type-datatypes
        if (s, self.shaclNS.datatype, None) in g:
            datatype = g.value(subject=s, predicate=self.shaclNS.datatype)
            if p in {self.shaclNS.minInclusive, self.shaclNS.maxInclusive,
                     self.shaclNS.minExclusive, self.shaclNS.maxExclusive} \
                        and datatype in {self.XSDNS.string, self.XSDNS.NMTOKEN, self.XSDNS.Name, self.XSDNS.language,
                                     self.XSDNS.anyURI, self.XSDNS.hexBinary, self.XSDNS.base64Binary}:
                return
            if p in {self.shaclNS.minLength, self.shaclNS.maxLength} \
                        and datatype in {self.XSDNS.integer, self.XSDNS.decimal, self.XSDNS.double, self.XSDNS.long,
                                     self.XSDNS.nonNegativeInteger, self.XSDNS.positiveInteger,
                                     self.XSDNS.nonPositiveInteger, self.XSDNS.negativeInteger, self.XSDNS.int,
                                     self.XSDNS.short, self.XSDNS.byte, self.XSDNS.unsignedLong, self.XSDNS.unsignedInt,
                                     self.XSDNS.unsignedShort, self.XSDNS.unsignedByte, self.XSDNS.time,
                                     self.XSDNS.duration, self.XSDNS.dayTimeDuration, self.XSDNS.yearMonthDuration,
                                     self.XSDNS.gMonthDay, self.XSDNS.gYearMonth, self.XSDNS.gDay, self.XSDNS.gMonth,
                                     self.XSDNS.gYear, self.XSDNS.dateTime, self.XSDNS.date, self.XSDNS.boolean}:
                return

        # check for bounded constraints if they don't conflict with bounded counterparts
        # e.g. maxConstraint = 10 is already present -> only allow minConstraint <= 10
        if p == self.shaclNS.minInclusive:
            if (s, self.shaclNS.maxInclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxInclusive)
                if o > counterRestriction:
                    return
            if (s, self.shaclNS.maxExclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxExclusive)
                if o >= counterRestriction:
                    return
            if (s, self.shaclNS.minExclusive, None) in g:
                return
        elif p == self.shaclNS.maxInclusive:
            if (s, self.shaclNS.minInclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minInclusive)
                if o < counterRestriction:
                    return
            if (s, self.shaclNS.minExclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minExclusive)
                if o <= counterRestriction:
                    return
            if (s, self.shaclNS.maxExclusive, None) in g:
                return
        elif p == self.shaclNS.minExclusive:
            if (s, self.shaclNS.maxExclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxExclusive)
                if o >= counterRestriction:
                    return
            if (s, self.shaclNS.maxInclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxInclusive)
                if o >= counterRestriction:
                    return
            if (s, self.shaclNS.minInclusive, None) in g:
                return
        elif p == self.shaclNS.maxExclusive:
            if (s, self.shaclNS.minExclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minExclusive)
                if o <= counterRestriction:
                    return
            if (s, self.shaclNS.minInclusive, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minInclusive)
                if o <= counterRestriction:
                    return
            if (s, self.shaclNS.maxInclusive, None) in g:
                return
        elif p == self.shaclNS.minLength:
            if (s, self.shaclNS.maxLength, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxLength)
                if o > counterRestriction:
                    return
        elif p == self.shaclNS.maxLength:
            if (s, self.shaclNS.minLength, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minLength)
                if o < counterRestriction:
                    return
        elif p == self.shaclNS.minOccurs:
            if (s, self.shaclNS.maxOccurs, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.maxOccurs)
                if o > counterRestriction:
                    return
        elif p == self.shaclNS.maxOccurs:
            if (s, self.shaclNS.minOccurs, None) in g:
                counterRestriction = g.value(subject=s, predicate=self.shaclNS.minOccurs)
                if o < counterRestriction:
                    return

        # add constraint since it passed all checks
        self.updateStats(p)
        g.add((s, p, o))

    def updateStats(self, p):
        # function made to generate dictionary that displays which constraints we enriched the shape with
        if p in self.enrich_stats:
            self.enrich_stats[p] += 1
        else:
            self.enrich_stats[p] = 1
