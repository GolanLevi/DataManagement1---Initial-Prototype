import { BufferGeometry, Uint16BufferAttribute, Uint32BufferAttribute } from '/static/js/three.module.js';

function toTrianglesDrawMode( geometry, drawMode ) {

    if ( drawMode === 4 /* triangles */ ) {
        return geometry;
    }

    const index = geometry.getIndex();

    // generate index if not present

    if ( index === null ) {

        const indices = [];

        const position = geometry.getAttribute( 'position' );

        if ( position !== undefined ) {

            for ( let i = 0; i < position.count; i ++ ) {

                indices.push( i );

            }

            geometry.setIndex( indices );

        } else {

            console.error( 'THREE.BufferGeometryUtils.toTrianglesDrawMode(): Undefined position attribute. Processing not possible.' );

            return geometry;

        }

    }

    //

    const numberOfTriangles = ( index.count - 2 );
    const newIndices = [];

    if ( drawMode === 5 /* triangle strip */ ) {

        // gl.TRIANGLE_STRIP

        for ( let i = 0; i < numberOfTriangles; i ++ ) {

            if ( i % 2 === 0 ) {

                newIndices.push( index.getX( i ) );
                newIndices.push( index.getX( i + 1 ) );
                newIndices.push( index.getX( i + 2 ) );

            } else {

                newIndices.push( index.getX( i + 1 ) );
                newIndices.push( index.getX( i ) );
                newIndices.push( index.getX( i + 2 ) );

            }

        }

    } else {

        // gl.TRIANGLE_FAN

        for ( let i = 1; i < numberOfTriangles + 1; i ++ ) {

            newIndices.push( index.getX( 0 ) );
            newIndices.push( index.getX( i ) );
            newIndices.push( index.getX( i + 1 ) );

        }

    }

    if ( ( newIndices.length / 3 ) !== numberOfTriangles ) {

        console.error( 'THREE.BufferGeometryUtils.toTrianglesDrawMode(): Unable to generate correct amount of triangles.' );

    }

    const newGeometry = geometry.clone();
    newGeometry.setIndex( ( newGeometry.getAttribute( 'position' ).count > 65535 ) ? new Uint32BufferAttribute( newIndices, 1 ) : new Uint16BufferAttribute( newIndices, 1 ) );

    return newGeometry;

}

export { toTrianglesDrawMode };
